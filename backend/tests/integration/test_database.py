"""Integration tests for database operations."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.project import Project
from app.schemas.project import ProjectStatus, SourceType


class TestDatabaseOperations:
    """Test database query operations."""

    def test_query_filter_by_status(self, test_db_session, project_factory):
        """Test filtering projects by status."""
        # Create projects with different statuses
        project1 = project_factory(name="Ready Project", status=ProjectStatus.ready)
        project2 = project_factory(name="Pending Project", status=ProjectStatus.pending)
        project3 = project_factory(name="Failed Project", status=ProjectStatus.failed)
        project4 = project_factory(name="Another Ready", status=ProjectStatus.ready)
        test_db_session.commit()

        # Query for ready projects
        ready_projects = test_db_session.query(Project).filter(
            Project.status == ProjectStatus.ready
        ).all()

        assert len(ready_projects) == 2
        assert all(p.status == ProjectStatus.ready for p in ready_projects)
        assert {p.name for p in ready_projects} == {"Ready Project", "Another Ready"}

        # Query for pending projects
        pending_projects = test_db_session.query(Project).filter(
            Project.status == ProjectStatus.pending
        ).all()

        assert len(pending_projects) == 1
        assert pending_projects[0].name == "Pending Project"

    def test_query_filter_by_name(self, test_db_session, project_factory):
        """Test filtering projects by name."""
        # Create projects
        project1 = project_factory(name="FastAPI Project")
        project2 = project_factory(name="Django Project")
        project3 = project_factory(name="FastAPI Example")
        test_db_session.commit()

        # Query for projects with "FastAPI" in name
        fastapi_projects = test_db_session.query(Project).filter(
            Project.name.like("%FastAPI%")
        ).all()

        assert len(fastapi_projects) == 2
        assert all("FastAPI" in p.name for p in fastapi_projects)

        # Exact match
        django_project = test_db_session.query(Project).filter(
            Project.name == "Django Project"
        ).first()

        assert django_project is not None
        assert django_project.name == "Django Project"

    def test_query_filter_by_source_type(self, test_db_session, project_factory):
        """Test filtering projects by source_type."""
        # Create projects with different source types
        project1 = project_factory(name="Git Project", source_type=SourceType.git_url)
        project2 = project_factory(name="Local Project", source_type=SourceType.local_path)
        project3 = project_factory(name="Another Git", source_type=SourceType.git_url)
        test_db_session.commit()

        # Query for git_url projects
        git_projects = test_db_session.query(Project).filter(
            Project.source_type == SourceType.git_url
        ).all()

        assert len(git_projects) == 2
        assert all(p.source_type == SourceType.git_url for p in git_projects)

        # Query for local_path projects
        local_projects = test_db_session.query(Project).filter(
            Project.source_type == SourceType.local_path
        ).all()

        assert len(local_projects) == 1
        assert local_projects[0].name == "Local Project"

    def test_pagination_offset_limit(self, test_db_session, project_factory):
        """Test pagination with offset and limit."""
        # Create 10 projects
        for i in range(10):
            project_factory(name=f"Project {i+1:02d}")
        test_db_session.commit()

        # First page (limit 3)
        page1 = test_db_session.query(Project).order_by(Project.name).limit(3).all()
        assert len(page1) == 3
        assert page1[0].name == "Project 01"
        assert page1[2].name == "Project 03"

        # Second page (offset 3, limit 3)
        page2 = test_db_session.query(Project).order_by(Project.name).offset(3).limit(3).all()
        assert len(page2) == 3
        assert page2[0].name == "Project 04"
        assert page2[2].name == "Project 06"

        # Last page (offset 9, limit 3)
        page_last = test_db_session.query(Project).order_by(Project.name).offset(9).limit(3).all()
        assert len(page_last) == 1
        assert page_last[0].name == "Project 10"

    def test_transaction_commit(self, test_db_session, project_factory):
        """Test transaction commit persists data."""
        # Create project
        project = project_factory(name="Test Project")

        # Before commit, changes are not visible in new query
        # (within same session they are visible)
        test_db_session.flush()

        # Commit transaction
        test_db_session.commit()

        # Query should find the project
        found = test_db_session.query(Project).filter(
            Project.name == "Test Project"
        ).first()

        assert found is not None
        assert found.name == "Test Project"

    def test_transaction_rollback(self, test_db_session):
        """Test transaction rollback discards changes."""
        from uuid import uuid4

        # Create project directly (don't use factory which commits)
        project = Project(
            id=str(uuid4()),
            name="Rollback Test",
            source_type=SourceType.local_path,
            source="/test/path",
            status=ProjectStatus.pending
        )
        test_db_session.add(project)
        test_db_session.flush()

        # Get ID before rollback
        project_id = project.id

        # Rollback transaction
        test_db_session.rollback()

        # Project should not exist after rollback
        found = test_db_session.query(Project).filter(
            Project.id == project_id
        ).first()

        assert found is None

    def test_update_project_in_transaction(self, test_db_session, project_factory):
        """Test updating project within transaction."""
        # Create and commit project
        project = project_factory(name="Original Name")
        test_db_session.commit()

        original_id = project.id

        # Update project
        project.name = "Updated Name"
        project.description = "New description"
        project.status = ProjectStatus.ready
        test_db_session.commit()

        # Verify updates persisted
        updated = test_db_session.query(Project).filter(
            Project.id == original_id
        ).first()

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "New description"
        assert updated.status == ProjectStatus.ready

    def test_delete_project_in_transaction(self, test_db_session, project_factory):
        """Test deleting project within transaction."""
        # Create projects
        project1 = project_factory(name="Keep This")
        project2 = project_factory(name="Delete This")
        test_db_session.commit()

        project2_id = project2.id

        # Delete project2
        test_db_session.delete(project2)
        test_db_session.commit()

        # Verify project2 is deleted
        deleted = test_db_session.query(Project).filter(
            Project.id == project2_id
        ).first()

        assert deleted is None

        # Verify project1 still exists
        kept = test_db_session.query(Project).filter(
            Project.name == "Keep This"
        ).first()

        assert kept is not None

    def test_order_by_created_at(self, test_db_session, project_factory):
        """Test ordering projects by created_at."""
        # Create projects with different timestamps
        now = datetime.utcnow()

        project1 = project_factory(name="Oldest")
        project1.created_at = now - timedelta(days=3)

        project2 = project_factory(name="Middle")
        project2.created_at = now - timedelta(days=1)

        project3 = project_factory(name="Newest")
        project3.created_at = now

        test_db_session.commit()

        # Order ascending (oldest first)
        ascending = test_db_session.query(Project).order_by(Project.created_at.asc()).all()
        assert len(ascending) == 3
        assert ascending[0].name == "Oldest"
        assert ascending[2].name == "Newest"

        # Order descending (newest first)
        descending = test_db_session.query(Project).order_by(Project.created_at.desc()).all()
        assert len(descending) == 3
        assert descending[0].name == "Newest"
        assert descending[2].name == "Oldest"

    def test_complex_query_multiple_filters(self, test_db_session, project_factory):
        """Test complex query with multiple filters."""
        # Create projects
        project1 = project_factory(
            name="FastAPI Ready",
            status=ProjectStatus.ready,
            source_type=SourceType.git_url
        )
        project2 = project_factory(
            name="FastAPI Pending",
            status=ProjectStatus.pending,
            source_type=SourceType.git_url
        )
        project3 = project_factory(
            name="Django Ready",
            status=ProjectStatus.ready,
            source_type=SourceType.local_path
        )
        test_db_session.commit()

        # Query: ready AND git_url AND name contains "FastAPI"
        results = test_db_session.query(Project).filter(
            Project.status == ProjectStatus.ready,
            Project.source_type == SourceType.git_url,
            Project.name.like("%FastAPI%")
        ).all()

        assert len(results) == 1
        assert results[0].name == "FastAPI Ready"

    def test_count_projects(self, test_db_session, project_factory):
        """Test counting projects with filters."""
        # Create projects
        for i in range(5):
            project_factory(name=f"Ready {i}", status=ProjectStatus.ready)

        for i in range(3):
            project_factory(name=f"Pending {i}", status=ProjectStatus.pending)

        test_db_session.commit()

        # Total count
        total = test_db_session.query(Project).count()
        assert total == 8

        # Count by status
        ready_count = test_db_session.query(Project).filter(
            Project.status == ProjectStatus.ready
        ).count()
        assert ready_count == 5

        pending_count = test_db_session.query(Project).filter(
            Project.status == ProjectStatus.pending
        ).count()
        assert pending_count == 3
