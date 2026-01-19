"""Unit tests for chat database models."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.project import Project
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.schemas.project import ProjectStatus, SourceType


class TestChatSessionModel:
    """Test ChatSession model."""

    @pytest.fixture
    def test_project(self, test_db_session):
        """Create a test project for chat sessions."""
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            source_type=SourceType.local_path,
            source="/path/to/project",
            status=ProjectStatus.ready
        )
        test_db_session.add(project)
        test_db_session.commit()
        return project

    def test_chat_session_creation(self, test_db_session, test_project):
        """Test creating a ChatSession model instance."""
        session_id = str(uuid4())
        session = ChatSession(
            id=session_id,
            project_id=test_project.id,
            title="Test Conversation"
        )

        test_db_session.add(session)
        test_db_session.commit()
        test_db_session.refresh(session)

        assert session.id == session_id
        assert session.project_id == test_project.id
        assert session.title == "Test Conversation"
        assert session.is_active is True
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_chat_session_default_values(self, test_db_session, test_project):
        """Test ChatSession model default values."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id
        )

        test_db_session.add(session)
        test_db_session.commit()
        test_db_session.refresh(session)

        assert session.title is None
        assert session.is_active is True

    def test_chat_session_to_dict(self, test_db_session, test_project):
        """Test ChatSession to_dict method."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id,
            title="Test Session"
        )

        test_db_session.add(session)
        test_db_session.commit()
        test_db_session.refresh(session)

        result = session.to_dict()

        assert "id" in result
        assert "project_id" in result
        assert "title" in result
        assert "is_active" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "messages" not in result  # Not included by default

    def test_chat_session_to_dict_with_messages(self, test_db_session, test_project):
        """Test ChatSession to_dict with messages included."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id,
            title="Test Session"
        )
        test_db_session.add(session)
        test_db_session.commit()

        # Add a message
        message = ChatMessage(
            id=str(uuid4()),
            session_id=session.id,
            role=MessageRole.user,
            content="Hello"
        )
        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(session)

        result = session.to_dict(include_messages=True)

        assert "messages" in result
        assert len(result["messages"]) == 1

    def test_chat_session_repr(self, test_db_session, test_project):
        """Test ChatSession __repr__ method."""
        session = ChatSession(
            id="test-id",
            project_id=test_project.id,
            title="My Chat"
        )

        repr_str = repr(session)

        assert "test-id" in repr_str
        assert "My Chat" in repr_str


class TestChatMessageModel:
    """Test ChatMessage model."""

    @pytest.fixture
    def test_project(self, test_db_session):
        """Create a test project."""
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            source_type=SourceType.local_path,
            source="/path/to/project",
            status=ProjectStatus.ready
        )
        test_db_session.add(project)
        test_db_session.commit()
        return project

    @pytest.fixture
    def test_session(self, test_db_session, test_project):
        """Create a test chat session."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id
        )
        test_db_session.add(session)
        test_db_session.commit()
        return session

    def test_chat_message_creation(self, test_db_session, test_session):
        """Test creating a ChatMessage model instance."""
        message_id = str(uuid4())
        message = ChatMessage(
            id=message_id,
            session_id=test_session.id,
            role=MessageRole.user,
            content="How does authentication work?"
        )

        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)

        assert message.id == message_id
        assert message.session_id == test_session.id
        assert message.role == MessageRole.user
        assert message.content == "How does authentication work?"
        assert message.sources is None
        assert message.created_at is not None

    def test_chat_message_with_sources(self, test_db_session, test_session):
        """Test ChatMessage with source citations."""
        sources = [
            {
                "file_path": "src/auth/middleware.py",
                "start_line": 45,
                "end_line": 67,
                "snippet": "def verify_token(token)...",
                "relevance_score": 0.92
            }
        ]

        message = ChatMessage(
            id=str(uuid4()),
            session_id=test_session.id,
            role=MessageRole.assistant,
            content="Authentication uses JWT tokens...",
            sources=sources
        )

        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)

        assert message.sources is not None
        assert len(message.sources) == 1
        assert message.sources[0]["file_path"] == "src/auth/middleware.py"

    def test_chat_message_roles(self, test_db_session, test_session):
        """Test all message roles."""
        roles = [MessageRole.user, MessageRole.assistant, MessageRole.system]

        for role in roles:
            message = ChatMessage(
                id=str(uuid4()),
                session_id=test_session.id,
                role=role,
                content=f"Test {role.value} message"
            )
            test_db_session.add(message)
            test_db_session.commit()
            test_db_session.refresh(message)

            assert message.role == role

    def test_chat_message_to_dict(self, test_db_session, test_session):
        """Test ChatMessage to_dict method."""
        message = ChatMessage(
            id=str(uuid4()),
            session_id=test_session.id,
            role=MessageRole.user,
            content="Test message"
        )

        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)

        result = message.to_dict()

        assert "id" in result
        assert "session_id" in result
        assert "role" in result
        assert "content" in result
        assert "sources" in result
        assert "created_at" in result

    def test_chat_message_repr(self, test_db_session, test_session):
        """Test ChatMessage __repr__ method with long content."""
        long_content = "This is a very long message " * 10
        message = ChatMessage(
            id="msg-id",
            session_id=test_session.id,
            role=MessageRole.user,
            content=long_content
        )

        repr_str = repr(message)

        assert "msg-id" in repr_str
        assert "..." in repr_str  # Should be truncated


class TestChatSessionMessageRelationship:
    """Test relationship between ChatSession and ChatMessage."""

    @pytest.fixture
    def test_project(self, test_db_session):
        """Create a test project."""
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            source_type=SourceType.local_path,
            source="/path/to/project",
            status=ProjectStatus.ready
        )
        test_db_session.add(project)
        test_db_session.commit()
        return project

    def test_session_messages_relationship(self, test_db_session, test_project):
        """Test that session.messages returns related messages."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id
        )
        test_db_session.add(session)
        test_db_session.commit()

        # Add multiple messages
        for i in range(3):
            message = ChatMessage(
                id=str(uuid4()),
                session_id=session.id,
                role=MessageRole.user if i % 2 == 0 else MessageRole.assistant,
                content=f"Message {i}"
            )
            test_db_session.add(message)

        test_db_session.commit()
        test_db_session.refresh(session)

        assert len(session.messages) == 3

    def test_cascade_delete(self, test_db_session, test_project):
        """Test that deleting a session deletes its messages."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id
        )
        test_db_session.add(session)
        test_db_session.commit()

        message = ChatMessage(
            id=str(uuid4()),
            session_id=session.id,
            role=MessageRole.user,
            content="Test message"
        )
        test_db_session.add(message)
        test_db_session.commit()

        message_id = message.id

        # Delete session
        test_db_session.delete(session)
        test_db_session.commit()

        # Message should also be deleted
        deleted_message = test_db_session.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()

        assert deleted_message is None

    def test_message_session_backref(self, test_db_session, test_project):
        """Test that message.session returns the parent session."""
        session = ChatSession(
            id=str(uuid4()),
            project_id=test_project.id,
            title="Test Session"
        )
        test_db_session.add(session)
        test_db_session.commit()

        message = ChatMessage(
            id=str(uuid4()),
            session_id=session.id,
            role=MessageRole.user,
            content="Test"
        )
        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)

        assert message.session is not None
        assert message.session.title == "Test Session"
