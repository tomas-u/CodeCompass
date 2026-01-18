"""Diagram generator service for creating Mermaid diagrams."""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4
from collections import defaultdict

from app.services.analyzer.dependency_graph import DependencyGraph
from app.schemas.diagram import DiagramType

logger = logging.getLogger(__name__)


# Language color mapping for Mermaid styling
LANGUAGE_COLORS = {
    "Python": "#3572A5",      # Blue
    "JavaScript": "#F7DF1E",  # Yellow
    "TypeScript": "#3178C6",  # Purple/Blue
    "TSX": "#3178C6",         # Purple/Blue (same as TypeScript)
    "default": "#CCCCCC"      # Gray for unknown
}

# Mermaid-safe color classes
LANGUAGE_STYLES = {
    "Python": "fill:#3572A5,stroke:#2b5d87,color:#fff",
    "JavaScript": "fill:#F7DF1E,stroke:#c4b018,color:#000",
    "TypeScript": "fill:#3178C6,stroke:#2563a0,color:#fff",
    "TSX": "fill:#3178C6,stroke:#2563a0,color:#fff",
    "default": "fill:#CCCCCC,stroke:#999999,color:#000"
}

# Circular dependency highlight style
CIRCULAR_STYLE = "fill:#FF6B6B,stroke:#CC5555,color:#fff"
CIRCULAR_EDGE_STYLE = "stroke:#FF0000,stroke-width:2px"


class DiagramGenerator:
    """
    Generate Mermaid diagrams from code analysis data.

    Supports:
    - Dependency diagrams from DependencyGraph
    - Color coding by language
    - Circular dependency highlighting
    - Large graph simplification via directory grouping
    """

    # Threshold for grouping nodes by directory
    GROUPING_THRESHOLD = 50

    def __init__(self):
        """Initialize the diagram generator."""
        self._node_id_counter = 0

    def generate_dependency_diagram(
        self,
        dependency_graph: DependencyGraph,
        title: str = "Module Dependencies",
        group_by_directory: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate a Mermaid dependency diagram from a DependencyGraph.

        Args:
            dependency_graph: The dependency graph to visualize
            title: Title for the diagram
            group_by_directory: Whether to group nodes by directory.
                               If None, auto-decides based on node count.

        Returns:
            Dictionary containing:
            - id: Unique diagram ID
            - type: DiagramType.dependency
            - title: Diagram title
            - mermaid_code: Generated Mermaid code
            - metadata: Node mappings, colors, stats
        """
        graph = dependency_graph.graph
        num_nodes = graph.number_of_nodes()

        # Auto-decide grouping
        if group_by_directory is None:
            group_by_directory = num_nodes > self.GROUPING_THRESHOLD

        # Get circular dependencies for highlighting
        circular_deps = dependency_graph.detect_circular_dependencies()
        circular_nodes = self._get_circular_nodes(circular_deps)
        circular_edges = self._get_circular_edges(circular_deps)

        if group_by_directory and num_nodes > self.GROUPING_THRESHOLD:
            return self._generate_grouped_diagram(
                dependency_graph, title, circular_nodes, circular_edges
            )
        else:
            return self._generate_flat_diagram(
                dependency_graph, title, circular_nodes, circular_edges
            )

    def _generate_flat_diagram(
        self,
        dependency_graph: DependencyGraph,
        title: str,
        circular_nodes: Set[str],
        circular_edges: Set[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """Generate a flat (non-grouped) dependency diagram."""
        graph = dependency_graph.graph
        lines = ["graph TD"]
        metadata = {
            "nodes": {},
            "edges": [],
            "stats": {
                "total_nodes": graph.number_of_nodes(),
                "total_edges": graph.number_of_edges(),
                "circular_dependencies": len(circular_nodes) > 0
            },
            "colors": LANGUAGE_COLORS
        }

        # Track node IDs
        node_ids: Dict[str, str] = {}

        # Generate nodes
        for node in graph.nodes():
            node_data = graph.nodes[node]
            node_id = self._sanitize_node_id(node)
            node_ids[node] = node_id

            # Get display label (short name)
            label = self._get_display_label(node)
            language = node_data.get("language", "default")

            # Determine style
            is_circular = node in circular_nodes
            style = CIRCULAR_STYLE if is_circular else LANGUAGE_STYLES.get(
                language, LANGUAGE_STYLES["default"]
            )

            # Add node definition with quoted label to handle special chars
            lines.append(f'    {node_id}["{label}"]')

            # Store metadata
            metadata["nodes"][node_id] = {
                "file_path": node,
                "module_name": node_data.get("module_name", node),
                "language": language,
                "is_circular": is_circular,
                "imports_count": graph.out_degree(node),
                "imported_by_count": graph.in_degree(node)
            }

        # Add empty line before edges
        lines.append("")

        # Generate edges
        for source, target, edge_data in graph.edges(data=True):
            source_id = node_ids.get(source, self._sanitize_node_id(source))
            target_id = node_ids.get(target, self._sanitize_node_id(target))

            # Check if edge is part of circular dependency
            is_circular_edge = (source, target) in circular_edges

            if is_circular_edge:
                lines.append(f"    {source_id} -.->|cycle| {target_id}")
            else:
                lines.append(f"    {source_id} --> {target_id}")

            metadata["edges"].append({
                "source": source_id,
                "target": target_id,
                "source_file": source,
                "target_file": target,
                "is_circular": is_circular_edge
            })

        # Add styling
        lines.append("")
        lines.extend(self._generate_style_definitions(graph, node_ids, circular_nodes))

        mermaid_code = "\n".join(lines)

        return {
            "id": str(uuid4()),
            "type": DiagramType.dependency,
            "title": title,
            "mermaid_code": mermaid_code,
            "metadata": metadata
        }

    def _generate_grouped_diagram(
        self,
        dependency_graph: DependencyGraph,
        title: str,
        circular_nodes: Set[str],
        circular_edges: Set[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """Generate a grouped diagram for large codebases."""
        graph = dependency_graph.graph
        lines = ["graph TD"]
        metadata = {
            "nodes": {},
            "groups": {},
            "edges": [],
            "stats": {
                "total_nodes": graph.number_of_nodes(),
                "total_edges": graph.number_of_edges(),
                "grouped": True,
                "circular_dependencies": len(circular_nodes) > 0
            },
            "colors": LANGUAGE_COLORS
        }

        # Group nodes by directory
        groups: Dict[str, List[str]] = defaultdict(list)
        for node in graph.nodes():
            directory = str(Path(node).parent)
            if directory == ".":
                directory = "root"
            groups[directory].append(node)

        # Track group IDs
        group_ids: Dict[str, str] = {}
        node_to_group: Dict[str, str] = {}

        # Generate subgraphs for each directory
        for directory, nodes in sorted(groups.items()):
            group_id = self._sanitize_node_id(f"dir_{directory}")
            group_ids[directory] = group_id

            # Determine if group has circular nodes
            group_has_circular = any(n in circular_nodes for n in nodes)

            # Get primary language in group
            languages = [graph.nodes[n].get("language", "default") for n in nodes]
            primary_language = max(set(languages), key=languages.count)

            # Use quoted label for subgraph to handle special chars like []
            lines.append(f'    subgraph {group_id}["{directory}"]')

            for node in nodes:
                node_data = graph.nodes[node]
                node_id = self._sanitize_node_id(node)
                node_to_group[node] = group_id

                label = self._get_display_label(node)
                is_circular = node in circular_nodes

                # Use quoted label to handle special chars
                lines.append(f'        {node_id}["{label}"]')

                metadata["nodes"][node_id] = {
                    "file_path": node,
                    "module_name": node_data.get("module_name", node),
                    "language": node_data.get("language", "default"),
                    "group": directory,
                    "is_circular": is_circular
                }

            lines.append("    end")
            lines.append("")

            metadata["groups"][group_id] = {
                "directory": directory,
                "file_count": len(nodes),
                "primary_language": primary_language,
                "has_circular": group_has_circular
            }

        # Generate edges (between nodes, some may cross groups)
        for source, target, edge_data in graph.edges(data=True):
            source_id = self._sanitize_node_id(source)
            target_id = self._sanitize_node_id(target)

            is_circular_edge = (source, target) in circular_edges

            if is_circular_edge:
                lines.append(f"    {source_id} -.->|cycle| {target_id}")
            else:
                lines.append(f"    {source_id} --> {target_id}")

            metadata["edges"].append({
                "source": source_id,
                "target": target_id,
                "source_file": source,
                "target_file": target,
                "is_circular": is_circular_edge,
                "cross_group": node_to_group.get(source) != node_to_group.get(target)
            })

        # Add styling
        lines.append("")
        node_ids = {n: self._sanitize_node_id(n) for n in graph.nodes()}
        lines.extend(self._generate_style_definitions(graph, node_ids, circular_nodes))

        mermaid_code = "\n".join(lines)

        return {
            "id": str(uuid4()),
            "type": DiagramType.dependency,
            "title": title,
            "mermaid_code": mermaid_code,
            "metadata": metadata
        }

    def _generate_style_definitions(
        self,
        graph,
        node_ids: Dict[str, str],
        circular_nodes: Set[str]
    ) -> List[str]:
        """Generate Mermaid style definitions for nodes."""
        lines = []

        # Group nodes by their style
        style_groups: Dict[str, List[str]] = defaultdict(list)

        for node in graph.nodes():
            node_id = node_ids.get(node)
            if not node_id:
                continue

            if node in circular_nodes:
                style_groups["circular"].append(node_id)
            else:
                language = graph.nodes[node].get("language", "default")
                style_groups[language].append(node_id)

        # Generate style classes
        for style_name, node_list in style_groups.items():
            if not node_list:
                continue

            if style_name == "circular":
                style = CIRCULAR_STYLE
            else:
                style = LANGUAGE_STYLES.get(style_name, LANGUAGE_STYLES["default"])

            # Mermaid style syntax: style nodeId fill:#fff,stroke:#333
            for node_id in node_list:
                lines.append(f"    style {node_id} {style}")

        return lines

    def _sanitize_node_id(self, path: str) -> str:
        """
        Convert a file path to a valid Mermaid node ID.

        Mermaid node IDs must be alphanumeric with underscores.
        """
        # Replace path separators and dots with underscores
        node_id = re.sub(r'[/\\.]', '_', path)
        # Remove any remaining non-alphanumeric characters
        node_id = re.sub(r'[^a-zA-Z0-9_]', '', node_id)
        # Ensure it doesn't start with a number
        if node_id and node_id[0].isdigit():
            node_id = 'n_' + node_id
        # Ensure it's not empty
        if not node_id:
            self._node_id_counter += 1
            node_id = f"node_{self._node_id_counter}"

        return node_id

    def _get_display_label(self, path: str) -> str:
        """Get a short display label for a file path."""
        # Use just the filename
        name = Path(path).name
        # Escape double quotes since we use quoted strings in Mermaid
        name = name.replace('"', "'")
        return name

    def _get_circular_nodes(self, cycles: List[List[str]]) -> Set[str]:
        """Extract all nodes involved in circular dependencies."""
        nodes = set()
        for cycle in cycles:
            nodes.update(cycle)
        return nodes

    def _get_circular_edges(self, cycles: List[List[str]]) -> Set[Tuple[str, str]]:
        """Extract all edges involved in circular dependencies."""
        edges = set()
        for cycle in cycles:
            for i in range(len(cycle) - 1):
                edges.add((cycle[i], cycle[i + 1]))
        return edges

    def generate_directory_diagram(
        self,
        repo_path: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a directory structure diagram.

        Args:
            repo_path: Path to the repository
            max_depth: Maximum directory depth to show

        Returns:
            Dictionary with diagram data
        """
        lines = ["graph TD"]
        metadata = {"nodes": {}, "stats": {"type": "directory"}}

        root = Path(repo_path)
        root_id = "root"
        root_name = root.name.replace('"', "'")
        lines.append(f'    {root_id}["{root_name}"]')

        self._add_directory_nodes(
            lines, metadata, root, root_id, current_depth=0, max_depth=max_depth
        )

        # Style the root differently
        lines.append("")
        lines.append(f"    style {root_id} fill:#4CAF50,stroke:#388E3C,color:#fff")

        return {
            "id": str(uuid4()),
            "type": DiagramType.directory,
            "title": "Directory Structure",
            "mermaid_code": "\n".join(lines),
            "metadata": metadata
        }

    def _add_directory_nodes(
        self,
        lines: List[str],
        metadata: Dict,
        directory: Path,
        parent_id: str,
        current_depth: int,
        max_depth: int
    ):
        """Recursively add directory nodes to the diagram."""
        if current_depth >= max_depth:
            return

        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return

        dirs = [e for e in entries if e.is_dir() and not e.name.startswith('.')]
        files = [e for e in entries if e.is_file() and not e.name.startswith('.')]

        # Add directories
        for d in dirs[:10]:  # Limit to 10 dirs per level
            dir_id = self._sanitize_node_id(str(d.relative_to(directory.parent)))
            # Use quoted label to handle special chars like []
            lines.append(f'    {parent_id} --> {dir_id}["{d.name}/"]')
            metadata["nodes"][dir_id] = {"path": str(d), "type": "directory"}

            self._add_directory_nodes(
                lines, metadata, d, dir_id, current_depth + 1, max_depth
            )

        # Add files (limited)
        for f in files[:5]:  # Limit to 5 files per directory
            file_id = self._sanitize_node_id(str(f.relative_to(directory.parent)))
            # Use quoted label with () shape for files
            file_name = f.name.replace('"', "'")
            lines.append(f'    {parent_id} --> {file_id}("{file_name}")')
            metadata["nodes"][file_id] = {"path": str(f), "type": "file"}

        # Add ellipsis if there are more
        if len(dirs) > 10 or len(files) > 5:
            more_id = f"{parent_id}_more"
            remaining = max(0, len(dirs) - 10) + max(0, len(files) - 5)
            lines.append(f'    {parent_id} --> {more_id}["... +{remaining} more"]')


def create_diagram_generator() -> DiagramGenerator:
    """Factory function to create a DiagramGenerator instance."""
    return DiagramGenerator()
