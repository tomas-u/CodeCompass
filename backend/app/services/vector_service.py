"""Vector service for Qdrant operations."""

import logging
from typing import List, Optional, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.schemas.code_chunk import ChunkData, ChunkWithContent

logger = logging.getLogger(__name__)

# Collection name for code chunks
COLLECTION_NAME = "code_chunks"


class VectorService:
    """Service for managing vector embeddings in Qdrant."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        dimensions: int = None,
    ):
        """
        Initialize the vector service.

        Args:
            host: Qdrant host (defaults to settings)
            port: Qdrant port (defaults to settings)
            dimensions: Embedding dimensions (defaults to settings)
        """
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.dimensions = dimensions or settings.embedding_dimensions
        self._client: Optional[QdrantClient] = None

    def _get_client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            client = self._get_client()
            # Get collections list to check connectivity
            client.get_collections()
            return True
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return False

    async def ensure_collection(self) -> bool:
        """
        Ensure the code_chunks collection exists.

        Creates the collection if it doesn't exist.

        Returns:
            True if collection exists or was created, False on error
        """
        try:
            client = self._get_client()

            # Check if collection exists
            collections = client.get_collections().collections
            collection_names = [c.name for c in collections]

            if COLLECTION_NAME in collection_names:
                logger.debug(f"Collection {COLLECTION_NAME} already exists")
                return True

            # Create collection
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qmodels.VectorParams(
                    size=self.dimensions,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            logger.info(f"Created collection {COLLECTION_NAME} with {self.dimensions} dimensions")
            return True

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            return False

    async def upsert_chunks(
        self,
        chunks: List[ChunkData],
        embeddings: List[List[float]],
    ) -> int:
        """
        Insert or update chunks in Qdrant.

        Args:
            chunks: List of chunk data
            embeddings: List of embedding vectors (same order as chunks)

        Returns:
            Number of chunks upserted
        """
        if not chunks or not embeddings:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch")

        try:
            client = self._get_client()

            # Prepare points
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point = qmodels.PointStruct(
                    id=chunk.id,
                    vector=embedding,
                    payload={
                        "project_id": chunk.project_id,
                        "file_path": chunk.file_path,
                        "chunk_type": chunk.chunk_type.value,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language,
                        "content": chunk.content,
                        "content_hash": chunk.content_hash,
                    },
                )
                points.append(point)

            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch,
                )

            logger.info(f"Upserted {len(points)} chunks to Qdrant")
            return len(points)

        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise

    async def search(
        self,
        query_vector: List[float],
        project_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkWithContent]:
        """
        Search for similar chunks.

        Args:
            query_vector: Query embedding vector
            project_id: Project ID to search within
            limit: Maximum number of results
            filters: Additional filters (language, file_patterns, etc.)

        Returns:
            List of chunks with content and scores
        """
        try:
            client = self._get_client()

            # Build filter conditions
            must_conditions = [
                qmodels.FieldCondition(
                    key="project_id",
                    match=qmodels.MatchValue(value=project_id),
                )
            ]

            # Add optional filters
            if filters:
                if filters.get("languages"):
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key="language",
                            match=qmodels.MatchAny(any=filters["languages"]),
                        )
                    )
                if filters.get("chunk_types"):
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key="chunk_type",
                            match=qmodels.MatchAny(any=filters["chunk_types"]),
                        )
                    )

            # Build query filter
            query_filter = qmodels.Filter(must=must_conditions)

            # Search using query_points (new qdrant-client API)
            response = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )

            # Convert to ChunkWithContent
            chunks = []
            for result in response.points:
                payload = result.payload
                chunk = ChunkWithContent(
                    id=str(result.id),
                    project_id=payload["project_id"],
                    file_path=payload["file_path"],
                    chunk_type=payload["chunk_type"],
                    start_line=payload["start_line"],
                    end_line=payload["end_line"],
                    language=payload.get("language"),
                    content=payload["content"],
                    score=result.score,
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_project_chunks(self, project_id: str) -> int:
        """
        Delete all chunks for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of chunks deleted (approximate)
        """
        try:
            client = self._get_client()

            # Count before deletion
            count_before = await self._count_project_chunks(project_id)

            # Delete by filter
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="project_id",
                                match=qmodels.MatchValue(value=project_id),
                            )
                        ]
                    )
                ),
            )

            logger.info(f"Deleted {count_before} chunks for project {project_id}")
            return count_before

        except Exception as e:
            logger.error(f"Failed to delete project chunks: {e}")
            return 0

    async def _count_project_chunks(self, project_id: str) -> int:
        """Count chunks for a project."""
        try:
            client = self._get_client()

            result = client.count(
                collection_name=COLLECTION_NAME,
                count_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="project_id",
                            match=qmodels.MatchValue(value=project_id),
                        )
                    ]
                ),
            )
            return result.count

        except Exception as e:
            logger.warning(f"Failed to count chunks: {e}")
            return 0

    async def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection statistics."""
        try:
            client = self._get_client()
            info = client.get_collection(COLLECTION_NAME)

            return {
                "name": COLLECTION_NAME,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value if info.status else "unknown",
                "dimensions": self.dimensions,
            }

        except Exception as e:
            logger.warning(f"Failed to get collection info: {e}")
            return None
