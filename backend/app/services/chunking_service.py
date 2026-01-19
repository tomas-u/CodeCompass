"""Chunking service for splitting files into embeddable chunks."""

import os
import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Generator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.schemas.code_chunk import ChunkData, ChunkType
from app.models.code_chunk import CodeChunk
from app.services.analyzer.utils.language_detector import LanguageDetector
from app.services.analyzer.utils.gitignore_parser import GitignoreParser

logger = logging.getLogger(__name__)

# Chunking configuration
SMALL_FILE_THRESHOLD = 200  # Lines - files smaller than this are kept whole
CHUNK_SIZE = 150  # Lines per chunk for larger files
CHUNK_OVERLAP = 20  # Lines of overlap between chunks


class ChunkingService:
    """Service for chunking code files for embedding."""

    def __init__(self, max_file_size_mb: int = 10):
        """
        Initialize chunking service.

        Args:
            max_file_size_mb: Maximum file size to process in MB
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.language_detector = LanguageDetector()
        self.gitignore_parser = GitignoreParser(use_defaults=True)

    def chunk_file(
        self,
        file_path: str,
        content: str,
        language: Optional[str],
        project_id: str,
    ) -> List[ChunkData]:
        """
        Split a file into chunks.

        Args:
            file_path: Path to the file (relative to repo)
            content: File content
            language: Detected language
            project_id: Project ID

        Returns:
            List of ChunkData objects
        """
        lines = content.split('\n')
        total_lines = len(lines)

        chunks = []

        if total_lines < SMALL_FILE_THRESHOLD:
            # Small file - keep as single chunk
            chunk = self._create_chunk(
                project_id=project_id,
                file_path=file_path,
                content=content,
                start_line=1,
                end_line=total_lines,
                chunk_type=ChunkType.file,
                language=language,
            )
            chunks.append(chunk)
        else:
            # Large file - split into segments with overlap
            start = 0
            segment_num = 0

            while start < total_lines:
                end = min(start + CHUNK_SIZE, total_lines)
                segment_lines = lines[start:end]
                segment_content = '\n'.join(segment_lines)

                chunk = self._create_chunk(
                    project_id=project_id,
                    file_path=file_path,
                    content=segment_content,
                    start_line=start + 1,  # 1-indexed
                    end_line=end,
                    chunk_type=ChunkType.segment,
                    language=language,
                )
                chunks.append(chunk)

                # Move to next segment with overlap
                start = end - CHUNK_OVERLAP
                if start >= total_lines - CHUNK_OVERLAP:
                    break  # Avoid tiny trailing chunks
                segment_num += 1

        return chunks

    def _create_chunk(
        self,
        project_id: str,
        file_path: str,
        content: str,
        start_line: int,
        end_line: int,
        chunk_type: ChunkType,
        language: Optional[str],
    ) -> ChunkData:
        """Create a ChunkData object."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        chunk_id = str(uuid4())

        return ChunkData(
            id=chunk_id,
            project_id=project_id,
            file_path=file_path,
            chunk_type=chunk_type,
            start_line=start_line,
            end_line=end_line,
            language=language,
            content=content,
            content_hash=content_hash,
        )

    def collect_files(
        self,
        repo_path: str,
    ) -> Generator[tuple[str, str, str], None, None]:
        """
        Collect all files to chunk from a repository.

        Yields:
            Tuples of (relative_path, content, language)
        """
        repo_path = Path(repo_path)

        # Parse .gitignore
        self.gitignore_parser.parse_gitignore(str(repo_path))

        for root, dirs, files in os.walk(repo_path):
            root_path = Path(root)

            # Filter out ignored directories
            dirs[:] = [
                d for d in dirs
                if not self.gitignore_parser.should_ignore_dir(
                    str(root_path / d), str(repo_path)
                )
            ]

            for filename in files:
                file_path = root_path / filename

                # Check if should ignore
                if self.gitignore_parser.should_ignore(str(file_path), str(repo_path)):
                    continue

                # Check file size
                try:
                    if file_path.stat().st_size > self.max_file_size_bytes:
                        logger.debug(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue

                # Detect language
                language = self.language_detector.detect_language(str(file_path))
                if not language:
                    continue

                # Read content
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    logger.debug(f"Failed to read {file_path}: {e}")
                    continue

                # Skip empty files
                if not content.strip():
                    continue

                # Get relative path
                rel_path = str(file_path.relative_to(repo_path))

                yield rel_path, content, language

    async def chunk_project(
        self,
        project_id: str,
        repo_path: str,
        db: Session,
        embedding_provider,
        vector_service,
        batch_size: int = 50,
    ) -> int:
        """
        Chunk an entire project and store in vector database.

        Args:
            project_id: Project ID
            repo_path: Path to repository
            db: Database session
            embedding_provider: Provider for generating embeddings
            vector_service: Service for storing vectors
            batch_size: Number of chunks to process at once

        Returns:
            Total number of chunks created
        """
        logger.info(f"Starting chunking for project {project_id}")

        # Ensure collection exists
        await vector_service.ensure_collection()

        # Delete existing chunks for this project
        await vector_service.delete_project_chunks(project_id)

        # Also delete from SQLite
        db.query(CodeChunk).filter(CodeChunk.project_id == project_id).delete()
        db.commit()

        total_chunks = 0
        batch_chunks: List[ChunkData] = []
        files_processed = 0

        for rel_path, content, language in self.collect_files(repo_path):
            # Chunk the file
            file_chunks = self.chunk_file(
                file_path=rel_path,
                content=content,
                language=language,
                project_id=project_id,
            )

            batch_chunks.extend(file_chunks)
            files_processed += 1

            # Process batch when full
            if len(batch_chunks) >= batch_size:
                processed = await self._process_batch(
                    batch_chunks, db, embedding_provider, vector_service
                )
                total_chunks += processed
                batch_chunks = []
                logger.debug(f"Processed {total_chunks} chunks from {files_processed} files")

        # Process remaining chunks
        if batch_chunks:
            processed = await self._process_batch(
                batch_chunks, db, embedding_provider, vector_service
            )
            total_chunks += processed

        logger.info(f"Chunking complete: {total_chunks} chunks from {files_processed} files")
        return total_chunks

    async def _process_batch(
        self,
        chunks: List[ChunkData],
        db: Session,
        embedding_provider,
        vector_service,
    ) -> int:
        """
        Process a batch of chunks - generate embeddings and store.

        Args:
            chunks: Chunks to process
            db: Database session
            embedding_provider: Embedding provider
            vector_service: Vector storage service

        Returns:
            Number of chunks processed
        """
        if not chunks:
            return 0

        try:
            # Generate embeddings for chunk contents
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_provider.embed(texts)

            if not embeddings:
                logger.error("Embedding generation returned empty results")
                return 0

            # Store in Qdrant
            await vector_service.upsert_chunks(chunks, embeddings)

            # Store metadata in SQLite
            for chunk in chunks:
                db_chunk = CodeChunk(
                    id=chunk.id,
                    project_id=chunk.project_id,
                    file_path=chunk.file_path,
                    chunk_type=chunk.chunk_type,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    language=chunk.language,
                    content_hash=chunk.content_hash,
                )
                db.add(db_chunk)

            db.commit()
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to process chunk batch: {e}")
            db.rollback()
            raise
