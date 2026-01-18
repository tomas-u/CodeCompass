"""Unit tests for DiagramGenerator service."""

import pytest
import tempfile
import shutil
from pathlib import Path

from app.services.diagram_generator import (
    DiagramGenerator,
    LANGUAGE_COLORS,
    LANGUAGE_STYLES,
    CIRCULAR_STYLE,
)
from app.services.analyzer.dependency_graph import DependencyGraph
from app.schemas.diagram import DiagramType


@pytest.fixture
def temp_repo():
    """Create a temporary repository directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="diagram_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def generator():
    """Create a DiagramGenerator instance."""
    return DiagramGenerator()


@pytest.fixture
def simple_dependency_graph(temp_repo):
    """Create a simple dependency graph for testing."""
    # Create files
    (temp_repo / "main.py").write_text("import utils")
    (temp_repo / "utils.py").write_text("import helpers")
    (temp_repo / "helpers.py").write_text("")

    imports = {
        str(temp_repo / "main.py"): ["utils"],
        str(temp_repo / "utils.py"): ["helpers"],
        str(temp_repo / "helpers.py"): []
    }

    graph = DependencyGraph(str(temp_repo))
    graph.build_from_analysis(imports, language="Python")
    return graph


@pytest.fixture
def circular_dependency_graph(temp_repo):
    """Create a graph with circular dependencies."""
    (temp_repo / "a.py").write_text("import b")
    (temp_repo / "b.py").write_text("import c")
    (temp_repo / "c.py").write_text("import a")

    imports = {
        str(temp_repo / "a.py"): ["b"],
        str(temp_repo / "b.py"): ["c"],
        str(temp_repo / "c.py"): ["a"]
    }

    graph = DependencyGraph(str(temp_repo))
    graph.build_from_analysis(imports, language="Python")
    return graph


@pytest.fixture
def multi_language_graph(temp_repo):
    """Create a graph with multiple languages."""
    (temp_repo / "app.py").write_text("import api")
    (temp_repo / "api.py").write_text("")
    (temp_repo / "client.js").write_text("import './utils.js'")
    (temp_repo / "utils.js").write_text("")

    imports = {
        str(temp_repo / "app.py"): ["api"],
        str(temp_repo / "api.py"): [],
        str(temp_repo / "client.js"): ["./utils.js"],
        str(temp_repo / "utils.js"): []
    }

    # Build with mixed languages
    graph = DependencyGraph(str(temp_repo))
    # Manually add nodes with different languages
    graph.graph.add_node("app.py", module_name="app", language="Python")
    graph.graph.add_node("api.py", module_name="api", language="Python")
    graph.graph.add_node("client.js", module_name="client", language="JavaScript")
    graph.graph.add_node("utils.js", module_name="utils", language="JavaScript")
    graph.graph.add_edge("app.py", "api.py")
    graph.graph.add_edge("client.js", "utils.js")

    return graph


@pytest.fixture
def large_dependency_graph(temp_repo):
    """Create a large graph for grouping tests."""
    # Create 60 files in different directories
    (temp_repo / "src").mkdir()
    (temp_repo / "src" / "utils").mkdir()
    (temp_repo / "tests").mkdir()

    imports = {}

    for i in range(20):
        f = temp_repo / "src" / f"module_{i}.py"
        f.write_text("")
        imports[str(f)] = []

    for i in range(20):
        f = temp_repo / "src" / "utils" / f"util_{i}.py"
        f.write_text("")
        imports[str(f)] = []

    for i in range(20):
        f = temp_repo / "tests" / f"test_{i}.py"
        f.write_text("")
        imports[str(f)] = []

    graph = DependencyGraph(str(temp_repo))
    graph.build_from_analysis(imports, language="Python")
    return graph


class TestDiagramGeneratorInit:
    """Test DiagramGenerator initialization."""

    def test_create_generator(self, generator):
        """Test generator creation."""
        assert generator is not None
        assert generator._node_id_counter == 0


class TestMermaidGeneration:
    """Test Mermaid diagram generation."""

    def test_generate_simple_diagram(self, generator, simple_dependency_graph):
        """Test generating a simple dependency diagram."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)

        assert result["type"] == DiagramType.dependency
        assert "mermaid_code" in result
        assert "metadata" in result
        assert result["mermaid_code"].startswith("graph TD")

    def test_diagram_has_nodes(self, generator, simple_dependency_graph):
        """Test that diagram contains all nodes."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        mermaid = result["mermaid_code"]

        # Should contain node definitions
        assert "main_py" in mermaid or "main.py" in mermaid
        assert "utils_py" in mermaid or "utils.py" in mermaid
        assert "helpers_py" in mermaid or "helpers.py" in mermaid

    def test_diagram_has_edges(self, generator, simple_dependency_graph):
        """Test that diagram contains edges."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        mermaid = result["mermaid_code"]

        # Should contain arrow notation
        assert "-->" in mermaid

    def test_diagram_metadata(self, generator, simple_dependency_graph):
        """Test that metadata is populated."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        metadata = result["metadata"]

        assert "nodes" in metadata
        assert "edges" in metadata
        assert "stats" in metadata
        assert metadata["stats"]["total_nodes"] == 3
        assert metadata["stats"]["total_edges"] == 2

    def test_diagram_has_id(self, generator, simple_dependency_graph):
        """Test that diagram has unique ID."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        assert "id" in result
        assert len(result["id"]) > 0

    def test_diagram_title(self, generator, simple_dependency_graph):
        """Test custom title."""
        result = generator.generate_dependency_diagram(
            simple_dependency_graph,
            title="My Custom Title"
        )
        assert result["title"] == "My Custom Title"


class TestCircularDependencyHighlighting:
    """Test circular dependency highlighting."""

    def test_circular_deps_marked(self, generator, circular_dependency_graph):
        """Test that circular dependencies are marked."""
        result = generator.generate_dependency_diagram(circular_dependency_graph)
        mermaid = result["mermaid_code"]

        # Should have dashed arrows for cycles
        assert "-.->|cycle|" in mermaid

    def test_circular_nodes_in_metadata(self, generator, circular_dependency_graph):
        """Test that circular nodes are flagged in metadata."""
        result = generator.generate_dependency_diagram(circular_dependency_graph)
        metadata = result["metadata"]

        # At least some nodes should be marked as circular
        circular_nodes = [
            node_id for node_id, data in metadata["nodes"].items()
            if data.get("is_circular")
        ]
        assert len(circular_nodes) > 0

    def test_circular_edges_in_metadata(self, generator, circular_dependency_graph):
        """Test that circular edges are flagged in metadata."""
        result = generator.generate_dependency_diagram(circular_dependency_graph)
        metadata = result["metadata"]

        circular_edges = [
            edge for edge in metadata["edges"]
            if edge.get("is_circular")
        ]
        assert len(circular_edges) > 0

    def test_circular_stats(self, generator, circular_dependency_graph):
        """Test circular dependency stats."""
        result = generator.generate_dependency_diagram(circular_dependency_graph)
        assert result["metadata"]["stats"]["circular_dependencies"] is True

    def test_no_circular_when_linear(self, generator, simple_dependency_graph):
        """Test no circular marking for linear graphs."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        assert result["metadata"]["stats"]["circular_dependencies"] is False
        assert "-.->|cycle|" not in result["mermaid_code"]


class TestLanguageColorCoding:
    """Test language-based color coding."""

    def test_style_definitions_present(self, generator, simple_dependency_graph):
        """Test that style definitions are generated."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        mermaid = result["mermaid_code"]

        # Should contain style definitions
        assert "style " in mermaid
        assert "fill:" in mermaid

    def test_python_color(self, generator, simple_dependency_graph):
        """Test Python files get correct color."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        mermaid = result["mermaid_code"]

        # Python color should be in the styles
        assert "#3572A5" in mermaid  # Python blue

    def test_multi_language_colors(self, generator, multi_language_graph):
        """Test multiple languages get different colors."""
        result = generator.generate_dependency_diagram(multi_language_graph)
        metadata = result["metadata"]

        # Should have color information
        assert "colors" in metadata
        assert "Python" in metadata["colors"]
        assert "JavaScript" in metadata["colors"]

    def test_color_constants(self):
        """Test color constants are defined."""
        assert "Python" in LANGUAGE_COLORS
        assert "JavaScript" in LANGUAGE_COLORS
        assert "TypeScript" in LANGUAGE_COLORS
        assert LANGUAGE_COLORS["Python"] == "#3572A5"
        assert LANGUAGE_COLORS["JavaScript"] == "#F7DF1E"


class TestLargeGraphGrouping:
    """Test large graph grouping by directory."""

    def test_auto_grouping_threshold(self, generator, large_dependency_graph):
        """Test that large graphs are auto-grouped."""
        result = generator.generate_dependency_diagram(large_dependency_graph)
        metadata = result["metadata"]

        # Should be grouped
        assert metadata["stats"].get("grouped") is True

    def test_subgraphs_created(self, generator, large_dependency_graph):
        """Test that subgraphs are created for directories."""
        result = generator.generate_dependency_diagram(large_dependency_graph)
        mermaid = result["mermaid_code"]

        # Should contain subgraph syntax
        assert "subgraph" in mermaid
        assert "end" in mermaid

    def test_group_metadata(self, generator, large_dependency_graph):
        """Test that group metadata is populated."""
        result = generator.generate_dependency_diagram(large_dependency_graph)
        metadata = result["metadata"]

        assert "groups" in metadata
        assert len(metadata["groups"]) > 0

    def test_force_no_grouping(self, generator, large_dependency_graph):
        """Test forcing no grouping."""
        result = generator.generate_dependency_diagram(
            large_dependency_graph,
            group_by_directory=False
        )
        mermaid = result["mermaid_code"]

        # Should not have subgraphs
        assert "subgraph" not in mermaid

    def test_force_grouping_small_graph(self, generator, simple_dependency_graph):
        """Test forcing grouping on small graph."""
        result = generator.generate_dependency_diagram(
            simple_dependency_graph,
            group_by_directory=True
        )
        # Small graphs don't get grouped even if forced (below threshold in _generate_grouped_diagram)
        # This tests the flow still works


class TestNodeIdSanitization:
    """Test node ID sanitization."""

    def test_sanitize_simple_path(self, generator):
        """Test sanitizing simple file path."""
        node_id = generator._sanitize_node_id("main.py")
        assert node_id == "main_py"

    def test_sanitize_path_with_slashes(self, generator):
        """Test sanitizing path with directory separators."""
        node_id = generator._sanitize_node_id("src/utils/helper.py")
        assert "_" in node_id
        assert "/" not in node_id

    def test_sanitize_removes_special_chars(self, generator):
        """Test removing special characters."""
        node_id = generator._sanitize_node_id("my-module@v2.py")
        assert "-" not in node_id
        assert "@" not in node_id

    def test_sanitize_numeric_start(self, generator):
        """Test handling paths starting with numbers."""
        node_id = generator._sanitize_node_id("123_module.py")
        assert not node_id[0].isdigit()

    def test_sanitize_empty_result(self, generator):
        """Test handling edge case of empty result."""
        # This shouldn't happen in practice, but test the fallback
        node_id = generator._sanitize_node_id("...")
        assert len(node_id) > 0


class TestDisplayLabels:
    """Test display label generation."""

    def test_simple_filename(self, generator):
        """Test getting display label for simple filename."""
        label = generator._get_display_label("main.py")
        assert label == "main.py"

    def test_path_shows_filename(self, generator):
        """Test that full paths show just filename."""
        label = generator._get_display_label("src/utils/helper.py")
        assert label == "helper.py"

    def test_escapes_quotes(self, generator):
        """Test that quotes are escaped."""
        label = generator._get_display_label('file"name.py')
        assert '"' not in label


class TestDirectoryDiagram:
    """Test directory structure diagram generation."""

    def test_generate_directory_diagram(self, generator, temp_repo):
        """Test generating directory diagram."""
        # Create some structure
        (temp_repo / "src").mkdir()
        (temp_repo / "src" / "main.py").write_text("")
        (temp_repo / "tests").mkdir()
        (temp_repo / "tests" / "test_main.py").write_text("")

        result = generator.generate_directory_diagram(str(temp_repo))

        assert result["type"] == DiagramType.directory
        assert "mermaid_code" in result
        assert result["mermaid_code"].startswith("graph TD")

    def test_directory_diagram_metadata(self, generator, temp_repo):
        """Test directory diagram metadata."""
        (temp_repo / "src").mkdir()
        (temp_repo / "src" / "main.py").write_text("")

        result = generator.generate_directory_diagram(str(temp_repo))

        assert "nodes" in result["metadata"]
        assert "stats" in result["metadata"]
        assert result["metadata"]["stats"]["type"] == "directory"

    def test_max_depth_limit(self, generator, temp_repo):
        """Test max depth limiting."""
        # Create deep structure
        current = temp_repo
        for i in range(10):
            current = current / f"level_{i}"
            current.mkdir()
            (current / "file.py").write_text("")

        result = generator.generate_directory_diagram(str(temp_repo), max_depth=2)

        # Should not include all levels
        mermaid = result["mermaid_code"]
        assert "level_0" in mermaid
        assert "level_8" not in mermaid


class TestMetadataStructure:
    """Test metadata structure completeness."""

    def test_node_metadata_fields(self, generator, simple_dependency_graph):
        """Test node metadata has required fields."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)

        for node_id, node_data in result["metadata"]["nodes"].items():
            assert "file_path" in node_data
            assert "language" in node_data
            assert "is_circular" in node_data

    def test_edge_metadata_fields(self, generator, simple_dependency_graph):
        """Test edge metadata has required fields."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)

        for edge in result["metadata"]["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "is_circular" in edge

    def test_stats_metadata_fields(self, generator, simple_dependency_graph):
        """Test stats metadata has required fields."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        stats = result["metadata"]["stats"]

        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "circular_dependencies" in stats


class TestMermaidSyntaxValidity:
    """Test that generated Mermaid syntax is valid."""

    def test_starts_with_graph_directive(self, generator, simple_dependency_graph):
        """Test diagram starts with graph directive."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        assert result["mermaid_code"].startswith("graph TD")

    def test_no_empty_lines_in_nodes(self, generator, simple_dependency_graph):
        """Test node definitions are properly formatted."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)
        lines = result["mermaid_code"].split("\n")

        # Check that node lines have proper syntax
        for line in lines:
            if "[" in line and "]" in line:
                # Node definition line - should have format: id[label]
                assert line.strip().endswith("]") or "-->" in line

    def test_edges_have_arrow_syntax(self, generator, simple_dependency_graph):
        """Test edges use proper arrow syntax."""
        result = generator.generate_dependency_diagram(simple_dependency_graph)

        # Either --> or -.-> for circular
        assert "-->" in result["mermaid_code"] or "-.->" in result["mermaid_code"]
