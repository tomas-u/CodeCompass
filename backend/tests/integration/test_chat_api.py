"""Integration tests for Chat API endpoints."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.schemas.project import ProjectStatus, SourceType
from app.services.rag_service import RAGResponse
from app.schemas.code_chunk import ChunkWithContent, ChunkType


class TestChatAPI:
    """Tests for Chat API endpoints."""

    @pytest.fixture
    def mock_rag_service(self):
        """Create a mock RAG service."""
        mock = MagicMock()
        return mock

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_non_streaming(self, mock_get_rag, client, project_factory):
        """Test non-streaming chat endpoint."""
        # Create a project
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # Mock RAG service
        mock_rag = MagicMock()
        mock_rag.chat_with_context = AsyncMock(
            return_value=RAGResponse(
                content="This is the response",
                sources=[
                    ChunkWithContent(
                        id="chunk-1",
                        project_id=project.id,
                        file_path="main.py",
                        chunk_type=ChunkType.file,
                        start_line=1,
                        end_line=10,
                        content="def main(): pass",
                        score=0.9,
                    )
                ],
                prompt_tokens=100,
                completion_tokens=50,
            )
        )
        mock_get_rag.return_value = mock_rag

        # Send chat request
        response = client.post(
            f"/api/projects/{project.id}/chat",
            json={
                "message": "What does main do?",
                "options": {"stream": False},
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert "message_id" in data
        assert data["response"]["content"] == "This is the response"
        assert len(data["response"]["sources"]) == 1
        assert data["response"]["sources"][0]["file_path"] == "main.py"

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_streaming(self, mock_get_rag, client, project_factory):
        """Test streaming chat endpoint."""
        # Create a project
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # Mock RAG service streaming
        async def mock_stream(*args, **kwargs):
            yield {"type": "sources", "sources": []}
            yield {"type": "token", "content": "Hello"}
            yield {"type": "token", "content": " world"}
            yield {"type": "done"}

        mock_rag = MagicMock()
        mock_rag.chat_with_context_stream = mock_stream
        mock_get_rag.return_value = mock_rag

        # Send streaming chat request
        response = client.post(
            f"/api/projects/{project.id}/chat",
            json={
                "message": "Hello",
                "options": {"stream": True},
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events
        content = response.content.decode("utf-8")
        events = []
        current_event = {}

        for line in content.split("\n"):
            if line.startswith("event: "):
                current_event["event"] = line[7:]
            elif line.startswith("data: "):
                current_event["data"] = json.loads(line[6:])
                events.append(current_event)
                current_event = {}

        # Should have sources, tokens, and done events
        event_types = [e["event"] for e in events]
        assert "sources" in event_types
        assert "token" in event_types
        assert "done" in event_types

    def test_chat_project_not_found(self, client):
        """Test chat with non-existent project."""
        response = client.post(
            "/api/projects/nonexistent-id/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 404

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_with_session_id(self, mock_get_rag, client, project_factory):
        """Test chat with existing session ID."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        mock_rag = MagicMock()
        mock_rag.chat_with_context = AsyncMock(
            return_value=RAGResponse(
                content="Response",
                sources=[],
            )
        )
        mock_get_rag.return_value = mock_rag

        response = client.post(
            f"/api/projects/{project.id}/chat",
            json={
                "message": "Hello",
                "session_id": "existing-session-123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing-session-123"

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_with_custom_options(self, mock_get_rag, client, project_factory):
        """Test chat with custom options."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        mock_rag = MagicMock()
        mock_rag.chat_with_context = AsyncMock(
            return_value=RAGResponse(
                content="Response",
                sources=[],
            )
        )
        mock_get_rag.return_value = mock_rag

        response = client.post(
            f"/api/projects/{project.id}/chat",
            json={
                "message": "Hello",
                "options": {
                    "max_context_chunks": 10,
                    "include_sources": False,
                },
            },
        )

        assert response.status_code == 200

        # Verify options were passed to RAG service
        mock_rag.chat_with_context.assert_called_once()
        call_kwargs = mock_rag.chat_with_context.call_args.kwargs
        assert call_kwargs["max_chunks"] == 10
        assert call_kwargs["include_sources"] is False

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_response_format(self, mock_get_rag, client, project_factory):
        """Test chat response format."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        mock_rag = MagicMock()
        mock_rag.chat_with_context = AsyncMock(
            return_value=RAGResponse(
                content="Response with **markdown**",
                sources=[
                    ChunkWithContent(
                        id="1",
                        project_id=project.id,
                        file_path="test.py",
                        chunk_type=ChunkType.file,
                        start_line=1,
                        end_line=5,
                        content="# test",
                        score=0.85,
                    )
                ],
                prompt_tokens=50,
                completion_tokens=25,
            )
        )
        mock_get_rag.return_value = mock_rag

        response = client.post(
            f"/api/projects/{project.id}/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "response" in data
        assert data["response"]["format"] == "markdown"
        assert "tokens_used" in data["response"]
        assert data["response"]["tokens_used"]["prompt"] == 50
        assert data["response"]["tokens_used"]["completion"] == 25

        # Check source format
        source = data["response"]["sources"][0]
        assert "file_path" in source
        assert "start_line" in source
        assert "end_line" in source
        assert "snippet" in source
        assert "relevance_score" in source


class TestChatSessionsAPI:
    """Tests for Chat Sessions API endpoints."""

    def test_list_sessions(self, client, project_factory):
        """Test listing chat sessions."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.get(f"/api/projects/{project.id}/chat/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_list_sessions_project_not_found(self, client):
        """Test listing sessions for non-existent project."""
        response = client.get("/api/projects/nonexistent/chat/sessions")
        assert response.status_code == 404

    def test_delete_session(self, client, project_factory):
        """Test deleting a chat session."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.delete(
            f"/api/projects/{project.id}/chat/sessions/session-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session-123"

    def test_delete_session_project_not_found(self, client):
        """Test deleting session from non-existent project."""
        response = client.delete(
            "/api/projects/nonexistent/chat/sessions/session-123"
        )
        assert response.status_code == 404
