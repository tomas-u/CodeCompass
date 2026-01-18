"""Dependency graph builder for code analysis."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging

import networkx as nx

logger = logging.getLogger(__name__)


class DependencyGraph:
    """
    Build and analyze dependency graphs from code import analysis.

    This class creates a directed graph where:
    - Nodes represent files/modules
    - Edges represent import relationships (A -> B means A imports B)

    Features:
    - Resolve relative imports to absolute paths
    - Detect circular dependencies
    - Calculate dependency depth per module
    - Identify leaf nodes (no dependencies)
    - Identify root nodes (not imported by others)
    - Export to multiple formats (dict, DOT, JSON)
    """

    def __init__(self, repo_path: str):
        """
        Initialize dependency graph builder.

        Args:
            repo_path: Absolute path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.graph: nx.DiGraph = nx.DiGraph()
        self._file_to_module: Dict[str, str] = {}
        self._module_to_file: Dict[str, str] = {}

    def build_from_analysis(
        self,
        file_imports: Dict[str, List[str]],
        language: str = "Python"
    ) -> "DependencyGraph":
        """
        Build dependency graph from file analysis data.

        Args:
            file_imports: Dictionary mapping file paths to list of imports
                         e.g., {"src/main.py": ["os", "utils.helpers", "./config"]}
            language: Programming language for import resolution

        Returns:
            Self for method chaining
        """
        logger.info(f"Building dependency graph from {len(file_imports)} files")

        # First pass: Register all files as nodes
        for file_path in file_imports.keys():
            rel_path = self._get_relative_path(file_path)
            module_name = self._file_to_module_name(rel_path, language)

            self.graph.add_node(
                rel_path,
                module_name=module_name,
                file_path=file_path,
                language=language
            )
            self._file_to_module[rel_path] = module_name
            self._module_to_file[module_name] = rel_path

        # Second pass: Add edges for imports
        for file_path, imports in file_imports.items():
            source_rel_path = self._get_relative_path(file_path)
            source_dir = str(Path(source_rel_path).parent)

            for imp in imports:
                # Try to resolve the import to a file in the repository
                resolved = self._resolve_import(
                    imp,
                    source_dir,
                    language
                )

                if resolved and resolved in self.graph:
                    # Internal dependency - add edge
                    self.graph.add_edge(
                        source_rel_path,
                        resolved,
                        import_name=imp,
                        is_relative=imp.startswith(".")
                    )
                else:
                    # External dependency - store as node attribute
                    if source_rel_path in self.graph:
                        external = self.graph.nodes[source_rel_path].get(
                            "external_deps", []
                        )
                        if imp not in external:
                            external.append(imp)
                        self.graph.nodes[source_rel_path]["external_deps"] = external

        logger.info(
            f"Graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

        return self

    def _get_relative_path(self, file_path: str) -> str:
        """Convert absolute path to relative path from repo root."""
        try:
            abs_path = Path(file_path).resolve()
            return str(abs_path.relative_to(self.repo_path))
        except ValueError:
            # Already relative or outside repo
            return file_path

    def _file_to_module_name(self, rel_path: str, language: str) -> str:
        """
        Convert file path to module name.

        Examples:
            Python: "src/utils/helpers.py" -> "src.utils.helpers"
            JS/TS:  "src/utils/helpers.ts" -> "src/utils/helpers"
        """
        path = Path(rel_path)

        if language == "Python":
            # Remove .py extension and convert path separators to dots
            if path.suffix in (".py", ".pyi", ".pyw"):
                without_ext = str(path.with_suffix(""))
                # Handle __init__.py -> parent module
                if path.stem == "__init__":
                    without_ext = str(path.parent)
                return without_ext.replace(os.sep, ".").replace("/", ".")
            return rel_path

        elif language in ("JavaScript", "TypeScript", "TSX"):
            # For JS/TS, keep path structure but remove extension
            if path.suffix in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
                return str(path.with_suffix(""))
            return rel_path

        return rel_path

    def _resolve_import(
        self,
        import_name: str,
        source_dir: str,
        language: str
    ) -> Optional[str]:
        """
        Resolve an import to a file path in the repository.

        Args:
            import_name: The import string (e.g., "utils.helpers", "./config")
            source_dir: Directory of the importing file (relative to repo root)
            language: Programming language

        Returns:
            Relative file path if found in repo, None otherwise
        """
        if language == "Python":
            return self._resolve_python_import(import_name, source_dir)
        elif language in ("JavaScript", "TypeScript", "TSX"):
            return self._resolve_js_import(import_name, source_dir)
        return None

    def _resolve_python_import(
        self,
        import_name: str,
        source_dir: str
    ) -> Optional[str]:
        """
        Resolve Python import to file path.

        Handles:
        - Absolute imports: "utils.helpers" -> "utils/helpers.py"
        - Relative imports: ".config" -> "./config.py" (relative to source)
        """
        # Handle relative imports
        if import_name.startswith("."):
            return self._resolve_relative_python_import(import_name, source_dir)

        # Absolute import: convert dots to path separators
        path_parts = import_name.split(".")

        # Try different file extensions
        for ext in [".py", ".pyi"]:
            # Try as module file
            potential_path = os.path.join(*path_parts) + ext
            if potential_path in self._file_to_module:
                return potential_path

            # Try as package (__init__.py)
            init_path = os.path.join(*path_parts, "__init__" + ext)
            if init_path in self._file_to_module:
                return init_path

        # Check if it matches any registered module
        for rel_path, module in self._file_to_module.items():
            if module == import_name or module.endswith("." + import_name):
                return rel_path

        return None

    def _resolve_relative_python_import(
        self,
        import_name: str,
        source_dir: str
    ) -> Optional[str]:
        """Resolve Python relative import."""
        # Count leading dots
        dots = 0
        for char in import_name:
            if char == ".":
                dots += 1
            else:
                break

        # Get the module name after the dots
        module_part = import_name[dots:]

        # Navigate up directories based on dot count
        current_dir = Path(source_dir)
        for _ in range(dots - 1):  # -1 because first dot is current package
            current_dir = current_dir.parent

        # Build target path
        if module_part:
            path_parts = module_part.split(".")
            target_dir = current_dir / os.path.join(*path_parts)
        else:
            target_dir = current_dir

        # Try different file patterns
        for ext in [".py", ".pyi"]:
            # As file
            file_path = str(target_dir) + ext
            if file_path in self._file_to_module:
                return file_path

            # As package
            init_path = str(target_dir / ("__init__" + ext))
            if init_path in self._file_to_module:
                return init_path

        return None

    def _resolve_js_import(
        self,
        import_name: str,
        source_dir: str
    ) -> Optional[str]:
        """
        Resolve JavaScript/TypeScript import to file path.

        Handles:
        - Relative imports: "./utils", "../config"
        - Index files: "./utils" -> "./utils/index.ts"
        """
        # Skip npm packages (don't start with . or /)
        if not import_name.startswith(".") and not import_name.startswith("/"):
            return None

        # Handle relative imports
        if import_name.startswith("."):
            # Resolve relative to source directory
            if source_dir == ".":
                resolved = import_name[2:] if import_name.startswith("./") else import_name
            else:
                resolved = str(Path(source_dir) / import_name)

            # Normalize path
            resolved = os.path.normpath(resolved)
        else:
            resolved = import_name.lstrip("/")

        # Try different extensions
        extensions = [".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs"]

        for ext in extensions:
            # Try direct file
            file_path = resolved + ext
            if file_path in self._file_to_module:
                return file_path

            # Try index file
            index_path = os.path.join(resolved, "index" + ext)
            if index_path in self._file_to_module:
                return index_path

        # Check if exact path exists (already has extension)
        if resolved in self._file_to_module:
            return resolved

        return None

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect all circular dependencies in the graph.

        Returns:
            List of cycles, where each cycle is a list of file paths
            forming the circular dependency.

        Example:
            [["a.py", "b.py", "c.py", "a.py"]]  # a -> b -> c -> a
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            # Add the first node at the end to show complete cycle
            return [[*cycle, cycle[0]] for cycle in cycles]
        except nx.NetworkXError:
            return []

    def get_circular_dependencies_report(self) -> Dict[str, Any]:
        """
        Get detailed report of circular dependencies.

        Returns:
            Dictionary with cycle information
        """
        cycles = self.detect_circular_dependencies()

        return {
            "has_circular_dependencies": len(cycles) > 0,
            "count": len(cycles),
            "cycles": [
                {
                    "files": cycle,
                    "length": len(cycle) - 1  # -1 because first is repeated at end
                }
                for cycle in cycles
            ]
        }

    def calculate_dependency_depth(self) -> Dict[str, int]:
        """
        Calculate dependency depth for each module.

        Depth is the longest path from the node to any leaf node.
        Leaf nodes have depth 0.

        Returns:
            Dictionary mapping file paths to their dependency depth
        """
        depths: Dict[str, int] = {}

        # Get all leaf nodes (nodes with no outgoing edges)
        leaf_nodes = self.get_leaf_nodes()

        # Initialize leaf nodes with depth 0
        for leaf in leaf_nodes:
            depths[leaf] = 0

        # Use reverse topological sort for DAGs
        try:
            # For DAGs, we can compute efficiently
            for node in reversed(list(nx.topological_sort(self.graph))):
                if node not in depths:
                    successors = list(self.graph.successors(node))
                    if successors:
                        depths[node] = max(depths.get(s, 0) for s in successors) + 1
                    else:
                        depths[node] = 0
        except nx.NetworkXUnfeasible:
            # Graph has cycles - use BFS-based approach
            for node in self.graph.nodes():
                if node not in depths:
                    depths[node] = self._calculate_node_depth(node, set())

        return depths

    def _calculate_node_depth(
        self,
        node: str,
        visited: Set[str]
    ) -> int:
        """Calculate depth for a single node, handling cycles."""
        if node in visited:
            return 0  # Cycle detected, stop

        visited.add(node)
        successors = list(self.graph.successors(node))

        if not successors:
            return 0

        max_depth = 0
        for successor in successors:
            depth = self._calculate_node_depth(successor, visited.copy())
            max_depth = max(max_depth, depth)

        return max_depth + 1

    def get_leaf_nodes(self) -> List[str]:
        """
        Get all leaf nodes (files that don't import other internal files).

        Returns:
            List of file paths that have no outgoing edges
        """
        return [
            node for node in self.graph.nodes()
            if self.graph.out_degree(node) == 0
        ]

    def get_root_nodes(self) -> List[str]:
        """
        Get all root nodes (files that are not imported by others).

        These are typically entry points or main modules.

        Returns:
            List of file paths that have no incoming edges
        """
        return [
            node for node in self.graph.nodes()
            if self.graph.in_degree(node) == 0
        ]

    def get_module_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed metrics for each module.

        Returns:
            Dictionary mapping file paths to their metrics
        """
        depths = self.calculate_dependency_depth()

        metrics = {}
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]

            metrics[node] = {
                "module_name": node_data.get("module_name", node),
                "imports_count": self.graph.out_degree(node),
                "imported_by_count": self.graph.in_degree(node),
                "dependency_depth": depths.get(node, 0),
                "is_leaf": self.graph.out_degree(node) == 0,
                "is_root": self.graph.in_degree(node) == 0,
                "imports": list(self.graph.successors(node)),
                "imported_by": list(self.graph.predecessors(node)),
                "external_deps": node_data.get("external_deps", [])
            }

        return metrics

    def to_dict(self) -> Dict[str, Any]:
        """
        Export graph as dictionary.

        Returns:
            Dictionary representation of the graph
        """
        circular = self.get_circular_dependencies_report()
        depths = self.calculate_dependency_depth()

        nodes = []
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            nodes.append({
                "id": node,
                "module_name": node_data.get("module_name", node),
                "language": node_data.get("language", "Unknown"),
                "imports_count": self.graph.out_degree(node),
                "imported_by_count": self.graph.in_degree(node),
                "dependency_depth": depths.get(node, 0),
                "is_leaf": self.graph.out_degree(node) == 0,
                "is_root": self.graph.in_degree(node) == 0,
                "external_deps": node_data.get("external_deps", [])
            })

        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "import_name": data.get("import_name", ""),
                "is_relative": data.get("is_relative", False)
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "leaf_nodes": len(self.get_leaf_nodes()),
                "root_nodes": len(self.get_root_nodes()),
                "max_depth": max(depths.values()) if depths else 0,
                "avg_imports": (
                    sum(self.graph.out_degree(n) for n in self.graph.nodes()) /
                    self.graph.number_of_nodes()
                ) if self.graph.number_of_nodes() > 0 else 0
            },
            "circular_dependencies": circular
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Export graph as JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    def to_dot(self) -> str:
        """
        Export graph in DOT format (Graphviz).

        Returns:
            DOT format string for visualization
        """
        lines = ["digraph DependencyGraph {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box, style=filled, fillcolor=lightblue];")
        lines.append("")

        # Get metrics for coloring
        depths = self.calculate_dependency_depth()
        max_depth = max(depths.values()) if depths else 0

        # Add nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            label = node_data.get("module_name", node)

            # Color based on depth (darker = deeper)
            depth = depths.get(node, 0)
            if max_depth > 0:
                intensity = int(200 - (depth / max_depth) * 100)
            else:
                intensity = 200
            color = f"#{intensity:02x}{intensity:02x}ff"

            # Special colors for roots and leaves
            if self.graph.in_degree(node) == 0:
                color = "#90EE90"  # Light green for roots
            elif self.graph.out_degree(node) == 0:
                color = "#FFB6C1"  # Light pink for leaves

            safe_label = label.replace('"', '\\"')
            safe_node = node.replace('"', '\\"').replace("/", "_").replace(".", "_")
            lines.append(f'    "{safe_node}" [label="{safe_label}", fillcolor="{color}"];')

        lines.append("")

        # Add edges
        for source, target, data in self.graph.edges(data=True):
            safe_source = source.replace('"', '\\"').replace("/", "_").replace(".", "_")
            safe_target = target.replace('"', '\\"').replace("/", "_").replace(".", "_")

            # Style for relative imports
            style = "dashed" if data.get("is_relative") else "solid"
            lines.append(f'    "{safe_source}" -> "{safe_target}" [style={style}];')

        lines.append("}")
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the dependency graph.

        Returns:
            Summary dictionary with key statistics
        """
        depths = self.calculate_dependency_depth()
        circular = self.detect_circular_dependencies()

        return {
            "total_modules": self.graph.number_of_nodes(),
            "total_dependencies": self.graph.number_of_edges(),
            "leaf_nodes": self.get_leaf_nodes(),
            "root_nodes": self.get_root_nodes(),
            "max_dependency_depth": max(depths.values()) if depths else 0,
            "circular_dependencies_count": len(circular),
            "has_circular_dependencies": len(circular) > 0,
            "most_imported": self._get_most_imported(5),
            "most_dependencies": self._get_most_dependencies(5)
        }

    def _get_most_imported(self, n: int) -> List[Tuple[str, int]]:
        """Get top N most imported modules."""
        imported_counts = [
            (node, self.graph.in_degree(node))
            for node in self.graph.nodes()
        ]
        imported_counts.sort(key=lambda x: x[1], reverse=True)
        return imported_counts[:n]

    def _get_most_dependencies(self, n: int) -> List[Tuple[str, int]]:
        """Get top N modules with most dependencies."""
        dep_counts = [
            (node, self.graph.out_degree(node))
            for node in self.graph.nodes()
        ]
        dep_counts.sort(key=lambda x: x[1], reverse=True)
        return dep_counts[:n]

    def get_ego_graph(self, file_path: str) -> Dict[str, Any]:
        """
        Get the ego graph for a specific file - its direct imports and dependents.

        Args:
            file_path: The file to center the graph on (relative path)

        Returns:
            Dictionary with the file, its imports, and its dependents
        """
        if file_path not in self.graph:
            return {"error": f"File not found: {file_path}"}

        node_data = self.graph.nodes[file_path]

        # Get what this file imports (outgoing edges)
        imports = []
        for target in self.graph.successors(file_path):
            target_data = self.graph.nodes[target]
            imports.append({
                "file": target,
                "module_name": target_data.get("module_name", target),
                "language": target_data.get("language", "Unknown"),
            })

        # Get what imports this file (incoming edges)
        imported_by = []
        for source in self.graph.predecessors(file_path):
            source_data = self.graph.nodes[source]
            imported_by.append({
                "file": source,
                "module_name": source_data.get("module_name", source),
                "language": source_data.get("language", "Unknown"),
            })

        # Check if this file is part of any circular dependency
        circular_deps = self.detect_circular_dependencies()
        in_cycle = any(file_path in cycle for cycle in circular_deps)
        cycles_involved = [cycle for cycle in circular_deps if file_path in cycle]

        return {
            "file": file_path,
            "module_name": node_data.get("module_name", file_path),
            "language": node_data.get("language", "Unknown"),
            "imports": imports,
            "imports_count": len(imports),
            "imported_by": imported_by,
            "imported_by_count": len(imported_by),
            "external_deps": node_data.get("external_deps", []),
            "is_leaf": len(imports) == 0,
            "is_root": len(imported_by) == 0,
            "in_circular_dependency": in_cycle,
            "circular_cycles": cycles_involved,
        }

    def get_file_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all files with basic dependency info for search/selection.

        Returns:
            List of files with import counts
        """
        files = []
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            files.append({
                "file": node,
                "module_name": node_data.get("module_name", node),
                "language": node_data.get("language", "Unknown"),
                "imports_count": self.graph.out_degree(node),
                "imported_by_count": self.graph.in_degree(node),
            })
        # Sort by most connections (imports + imported_by)
        files.sort(key=lambda x: x["imports_count"] + x["imported_by_count"], reverse=True)
        return files
