"""RAG (Retrieval Augmented Generation) service for context-aware chat."""

import logging
from typing import List, Optional, Tuple, AsyncIterator, Dict, Any
from dataclasses import dataclass

from app.services.llm import get_embedding_provider, get_vector_service, get_llm_provider
from app.services.llm.base import ChatMessage as LLMChatMessage
from app.schemas.code_chunk import ChunkWithContent

logger = logging.getLogger(__name__)

# Default RAG configuration
DEFAULT_MAX_CHUNKS = 2  # Keep small to reduce prompt size and improve speed
DEFAULT_MIN_SCORE = 0.05  # Low threshold - semantic similarity scores can be low but still relevant
DEFAULT_MAX_RESPONSE_TOKENS = 512  # Limit response length for faster generation
DEFAULT_CONTEXT_WINDOW = 2048  # Smaller context window for faster processing


@dataclass
class RAGContext:
    """Context retrieved for RAG."""
    chunks: List[ChunkWithContent]
    query: str
    total_tokens_estimate: int = 0


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    content: str
    sources: List[ChunkWithContent]
    prompt_tokens: int = 0
    completion_tokens: int = 0


class RAGService:
    """Service for RAG operations."""

    def __init__(self):
        """Initialize RAG service."""
        self._embedding_provider = None
        self._vector_service = None
        self._llm_provider = None

    @property
    def embedding_provider(self):
        """Lazy load embedding provider."""
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider()
        return self._embedding_provider

    @property
    def vector_service(self):
        """Lazy load vector service."""
        if self._vector_service is None:
            self._vector_service = get_vector_service()
        return self._vector_service

    @property
    def llm_provider(self):
        """Lazy load LLM provider."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider()
        return self._llm_provider

    async def retrieve_context(
        self,
        query: str,
        project_id: str,
        max_chunks: int = DEFAULT_MAX_CHUNKS,
        min_score: float = DEFAULT_MIN_SCORE,
        filters: Optional[dict] = None,
    ) -> RAGContext:
        """
        Retrieve relevant context for a query.

        Args:
            query: User's question
            project_id: Project ID to search within
            max_chunks: Maximum number of chunks to retrieve
            min_score: Minimum relevance score (0-1)
            filters: Optional filters (languages, etc.)

        Returns:
            RAGContext with retrieved chunks
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_provider.embed_single(query)

            # Search for relevant chunks
            chunks = await self.vector_service.search(
                query_vector=query_embedding,
                project_id=project_id,
                limit=max_chunks,
                filters=filters,
            )

            # Filter by minimum score
            filtered_chunks = [
                chunk for chunk in chunks
                if chunk.score and chunk.score >= min_score
            ]

            # Estimate token count (rough: 1 token per 4 chars)
            total_chars = sum(len(c.content) for c in filtered_chunks)
            tokens_estimate = total_chars // 4

            return RAGContext(
                chunks=filtered_chunks,
                query=query,
                total_tokens_estimate=tokens_estimate,
            )

        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return RAGContext(chunks=[], query=query)

    def build_rag_prompt(
        self,
        query: str,
        project_name: str,
        chunks: List[ChunkWithContent],
    ) -> str:
        """
        Build a prompt with retrieved context.

        Args:
            query: User's question
            project_name: Name of the project
            chunks: Retrieved context chunks

        Returns:
            Formatted prompt string
        """
        if not chunks:
            # No context available - basic prompt
            return f"""You are an AI assistant helping developers understand a codebase.
You are analyzing a project called "{project_name}".

The user is asking about the codebase, but no relevant code context was found.
Please let the user know you don't have specific code context to reference,
but try to provide a helpful general response based on the question.

User's question: {query}"""

        # Build context section
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"""
--- File: {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}) ---
```{chunk.language or ''}
{chunk.content}
```
""")

        context_text = "\n".join(context_parts)

        prompt = f"""You are an AI assistant helping developers understand a codebase.
You are analyzing a project called "{project_name}".

I have retrieved the following relevant code context to help answer the question:

{context_text}

Instructions:
1. Use the provided code context to answer the user's question
2. Reference specific files and line numbers when relevant
3. Use markdown formatting for code snippets
4. If the context doesn't contain enough information, say so
5. Be concise but thorough
6. DO NOT fabricate any data or answers, only keep the facts you know for sure

User's question: {query}"""

        return prompt

    async def chat_with_context(
        self,
        query: str,
        project_id: str,
        project_name: str,
        max_chunks: int = DEFAULT_MAX_CHUNKS,
        include_sources: bool = True,
    ) -> RAGResponse:
        """
        Full RAG pipeline: retrieve context and generate response.

        Args:
            query: User's question
            project_id: Project ID
            project_name: Project name
            max_chunks: Maximum context chunks
            include_sources: Whether to include sources in response

        Returns:
            RAGResponse with content and sources
        """
        # Check if services are available
        embedding_healthy = await self.embedding_provider.health_check()
        vector_healthy = await self.vector_service.health_check()
        llm_healthy = await self.llm_provider.health_check()

        # If embedding/vector not available, fall back to non-RAG
        if not embedding_healthy or not vector_healthy:
            logger.warning("Embedding or vector service unavailable, using non-RAG response")
            return await self._non_rag_response(query, project_name, llm_healthy)

        # Retrieve context
        context = await self.retrieve_context(
            query=query,
            project_id=project_id,
            max_chunks=max_chunks,
        )

        logger.info(f"RAG context retrieved: {len(context.chunks)} chunks for query: '{query[:50]}...'")
        for i, chunk in enumerate(context.chunks):
            logger.info(f"  Chunk {i+1}: {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}, score: {chunk.score:.3f})")

        # Build prompt
        prompt = self.build_rag_prompt(
            query=query,
            project_name=project_name,
            chunks=context.chunks,
        )

        logger.debug(f"RAG prompt length: {len(prompt)} chars (~{len(prompt)//4} tokens)")

        # Check if LLM is available
        if not llm_healthy:
            logger.warning("LLM service unavailable")
            return RAGResponse(
                content="**LLM service is currently unavailable.** Please ensure Ollama is running.",
                sources=context.chunks if include_sources else [],
            )

        # Generate response
        try:
            messages = [
                LLMChatMessage(role="user", content=prompt),
            ]

            # Use limited tokens for faster response
            result = await self.llm_provider.chat(
                messages,
                max_tokens=DEFAULT_MAX_RESPONSE_TOKENS,
                num_ctx=DEFAULT_CONTEXT_WINDOW,
            )

            return RAGResponse(
                content=result.content,
                sources=context.chunks if include_sources else [],
                prompt_tokens=result.prompt_tokens or 0,
                completion_tokens=result.completion_tokens or 0,
            )

        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            return RAGResponse(
                content=f"**Error generating response:** {str(e)}",
                sources=context.chunks if include_sources else [],
            )

    async def chat_with_context_stream(
        self,
        query: str,
        project_id: str,
        project_name: str,
        max_chunks: int = DEFAULT_MAX_CHUNKS,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Full RAG pipeline with streaming: retrieve context and stream response.

        Args:
            query: User's question
            project_id: Project ID
            project_name: Project name
            max_chunks: Maximum context chunks

        Yields:
            Dict with type and data:
              - {"type": "sources", "sources": [...]} - Context sources
              - {"type": "token", "content": "..."} - Token from LLM
              - {"type": "done"} - Stream complete
              - {"type": "error", "message": "..."} - Error occurred
        """
        # Check if services are available
        embedding_healthy = await self.embedding_provider.health_check()
        vector_healthy = await self.vector_service.health_check()
        llm_healthy = await self.llm_provider.health_check()

        if not llm_healthy:
            yield {"type": "error", "message": "LLM service is currently unavailable. Please ensure Ollama is running."}
            return

        # Retrieve context (non-streaming)
        chunks: List[ChunkWithContent] = []
        if embedding_healthy and vector_healthy:
            context = await self.retrieve_context(
                query=query,
                project_id=project_id,
                max_chunks=max_chunks,
            )
            chunks = context.chunks
            logger.info(f"RAG streaming context retrieved: {len(chunks)} chunks")
        else:
            logger.warning("Embedding or vector service unavailable, streaming without RAG context")

        # Yield sources immediately
        sources_data = [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "snippet": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "relevance_score": chunk.score or 0.0,
            }
            for chunk in chunks
        ]
        yield {"type": "sources", "sources": sources_data}

        # Build prompt
        prompt = self.build_rag_prompt(
            query=query,
            project_name=project_name,
            chunks=chunks,
        )

        # Stream response from LLM
        try:
            messages = [
                LLMChatMessage(role="user", content=prompt),
            ]

            async for token in self.llm_provider.chat_stream(
                messages,
                max_tokens=DEFAULT_MAX_RESPONSE_TOKENS,
                num_ctx=DEFAULT_CONTEXT_WINDOW,
            ):
                yield {"type": "token", "content": token}

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"LLM streaming chat failed: {e}")
            yield {"type": "error", "message": str(e)}

    async def _non_rag_response(
        self,
        query: str,
        project_name: str,
        llm_available: bool,
    ) -> RAGResponse:
        """Generate response without RAG context."""
        if not llm_available:
            return RAGResponse(
                content="""**Note: LLM and embedding services are currently unavailable.**

Please ensure:
1. Ollama is running (`ollama serve`)
2. The embedding service is running
3. Qdrant is running

Then re-analyze the project to generate embeddings.""",
                sources=[],
            )

        # Use LLM without context
        prompt = f"""You are an AI assistant helping developers understand a codebase.
You are analyzing a project called "{project_name}".

Note: The code embedding service is currently unavailable, so I cannot search for specific code context.
I'll try to provide a helpful general response.

User's question: {query}"""

        try:
            messages = [
                LLMChatMessage(role="user", content=prompt),
            ]

            result = await self.llm_provider.chat(
                messages,
                max_tokens=DEFAULT_MAX_RESPONSE_TOKENS,
                num_ctx=DEFAULT_CONTEXT_WINDOW,
            )

            return RAGResponse(
                content=result.content + "\n\n*Note: Response generated without code context - embedding service unavailable.*",
                sources=[],
                prompt_tokens=result.prompt_tokens or 0,
                completion_tokens=result.completion_tokens or 0,
            )

        except Exception as e:
            logger.error(f"Non-RAG LLM call failed: {e}")
            return RAGResponse(
                content=f"**Error generating response:** {str(e)}",
                sources=[],
            )


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
