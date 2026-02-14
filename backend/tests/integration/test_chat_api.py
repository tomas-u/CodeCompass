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

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_streaming_persists_to_db(self, mock_get_rag, client, project_factory):
        """Test that streaming chat persists assistant message and sources to DB."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # Mock RAG service streaming with sources
        async def mock_stream(*args, **kwargs):
            yield {
                "type": "sources",
                "sources": [
                    {
                        "file_path": "main.py",
                        "start_line": 1,
                        "end_line": 10,
                        "snippet": "def main(): pass",
                        "relevance_score": 0.9,
                    }
                ],
            }
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

        # Extract session_id from the SSE session event
        content = response.content.decode("utf-8")
        session_id = None
        for line in content.split("\n"):
            if line.startswith("data: ") and "session_id" in line:
                data = json.loads(line[6:])
                if "session_id" in data:
                    session_id = data["session_id"]
                    break
        assert session_id is not None

        # Fetch the session and verify persistence
        get_response = client.get(
            f"/api/projects/{project.id}/chat/sessions/{session_id}"
        )
        assert get_response.status_code == 200
        messages = get_response.json()["messages"]

        # Find the streamed assistant message by expected content
        assistant_messages = [
            m for m in messages
            if m["role"] == "assistant" and m["content"] == "Hello world"
        ]
        assert len(assistant_messages) == 1

        # Verify sources were persisted
        sources = assistant_messages[0].get("sources")
        assert sources is not None
        assert len(sources) == 1
        assert sources[0]["file_path"] == "main.py"
        assert sources[0]["snippet"] == "def main(): pass"
        assert sources[0]["relevance_score"] == 0.9

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

        # First create a session
        create_response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]

        # Now chat with that session ID
        response = client.post(
            f"/api/projects/{project.id}/chat",
            json={
                "message": "Hello",
                "session_id": session_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

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

        # First create a session
        create_response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]

        # Now delete the session
        response = client.delete(
            f"/api/projects/{project.id}/chat/sessions/{session_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    def test_delete_session_project_not_found(self, client):
        """Test deleting session from non-existent project."""
        response = client.delete(
            "/api/projects/nonexistent/chat/sessions/session-123"
        )
        assert response.status_code == 404

    def test_delete_session_not_found(self, client, project_factory):
        """Test deleting non-existent session."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.delete(
            f"/api/projects/{project.id}/chat/sessions/nonexistent-session"
        )
        assert response.status_code == 404

    def test_create_session(self, client, project_factory):
        """Test creating a new chat session."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "messages" in data
        assert "created_at" in data
        # New sessions should have an intro message from the AI
        assert len(data["messages"]) >= 1

    def test_create_session_with_title(self, client, project_factory):
        """Test creating a session with custom title."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={"title": "My Custom Chat"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My Custom Chat"

    def test_create_session_project_not_found(self, client):
        """Test creating session for non-existent project."""
        response = client.post(
            "/api/projects/nonexistent/chat/sessions",
            json={},
        )
        assert response.status_code == 404

    def test_get_session(self, client, project_factory):
        """Test getting a specific chat session."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # First create a session
        create_response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={"title": "Test Session"},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]

        # Now get the session
        response = client.get(
            f"/api/projects/{project.id}/chat/sessions/{session_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "Test Session"
        assert "messages" in data
        assert "created_at" in data

    def test_get_session_not_found(self, client, project_factory):
        """Test getting non-existent session."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.get(
            f"/api/projects/{project.id}/chat/sessions/nonexistent-session"
        )
        assert response.status_code == 404

    def test_get_session_project_not_found(self, client):
        """Test getting session from non-existent project."""
        response = client.get(
            "/api/projects/nonexistent/chat/sessions/session-123"
        )
        assert response.status_code == 404

    def test_update_session_title(self, client, project_factory):
        """Test updating session title."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # First create a session
        create_response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]

        # Update the title
        response = client.patch(
            f"/api/projects/{project.id}/chat/sessions/{session_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

        # Verify the update
        get_response = client.get(
            f"/api/projects/{project.id}/chat/sessions/{session_id}"
        )
        assert get_response.json()["title"] == "Updated Title"

    def test_update_session_active_status(self, client, project_factory):
        """Test updating session active status."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # Create two sessions
        response1 = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )
        session1_id = response1.json()["id"]

        response2 = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )
        session2_id = response2.json()["id"]

        # Set first session as active
        response = client.patch(
            f"/api/projects/{project.id}/chat/sessions/{session1_id}",
            json={"is_active": True},
        )

        assert response.status_code == 200

    def test_update_session_not_found(self, client, project_factory):
        """Test updating non-existent session."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        response = client.patch(
            f"/api/projects/{project.id}/chat/sessions/nonexistent-session",
            json={"title": "New Title"},
        )
        assert response.status_code == 404

    def test_update_session_project_not_found(self, client):
        """Test updating session from non-existent project."""
        response = client.patch(
            "/api/projects/nonexistent/chat/sessions/session-123",
            json={"title": "New Title"},
        )
        assert response.status_code == 404

    def test_session_messages_persist(self, client, project_factory):
        """Test that messages are persisted in sessions."""
        from unittest.mock import patch, AsyncMock, MagicMock

        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # Create a session
        create_response = client.post(
            f"/api/projects/{project.id}/chat/sessions",
            json={},
        )
        session_id = create_response.json()["id"]
        initial_message_count = len(create_response.json()["messages"])

        # Send a chat message with mocked RAG
        with patch("app.api.routes.chat.get_rag_service") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.chat_with_context = AsyncMock(
                return_value=RAGResponse(
                    content="Test response",
                    sources=[],
                )
            )
            mock_get_rag.return_value = mock_rag

            chat_response = client.post(
                f"/api/projects/{project.id}/chat",
                json={
                    "message": "Test question",
                    "session_id": session_id,
                },
            )
            assert chat_response.status_code == 200

        # Get the session and verify messages were added
        get_response = client.get(
            f"/api/projects/{project.id}/chat/sessions/{session_id}"
        )
        assert get_response.status_code == 200
        messages = get_response.json()["messages"]

        # Should have: intro + user message + assistant response
        assert len(messages) == initial_message_count + 2

        # Check the user message
        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "Test question"

    def test_list_sessions_returns_multiple(self, client, project_factory):
        """Test listing multiple sessions."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready,
        )

        # Create multiple sessions
        for i in range(3):
            client.post(
                f"/api/projects/{project.id}/chat/sessions",
                json={"title": f"Session {i}"},
            )

        # List sessions
        response = client.get(f"/api/projects/{project.id}/chat/sessions")
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 3
        for item in data["items"]:
            assert "id" in item
            assert "title" in item
            assert "message_count" in item
            assert "created_at" in item
            assert "last_message_at" in item
