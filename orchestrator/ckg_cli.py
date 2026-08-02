"""CKG inspection CLI: change impact analysis and graph explorer.

python -m orchestrator.ckg_cli impact --product-dir products/bmi --module bmi --node REQ-002
python -m orchestrator.ckg_cli explore --product-dir products/bmi --module bmi [--json | --dot]
python -m orchestrator.ckg_cli show --product-dir products/bmi --module bmi --node REQ-002

Kept separate from orchestrator/cli.py (the pipeline-execution entrypoint used
by demo/bmi/run.sh) so graph inspection and pipeline execution stay
independently invocable — adding subcommands to cli.py would require changing
its existing `--name ... --requirement ...` invocation.

Every command rebuilds the graph fresh from the current on-disk artifacts
(orchestrator.ckg.build_graph) rather than reading a possibly-stale
evidence/ckg.json snapshot, so results always reflect the files as they are
right now.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import ckg, incremental
from .config import ProductSpec


def _add_product_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--product-dir", required=True, type=Path, help="e.g. products/bmi"
    )
    parser.add_argument(
        "--module", required=True, help="module name, e.g. 'bmi' (matches src/<module>.py)"
    )


def _node_line(node: ckg.Node) -> str:
    return f"{node.id} ({node.type})" + (f" — {node.label}" if node.label else "")


def _cmd_impact(args: argparse.Namespace) -> int:
    graph = ckg.build_graph(args.product_dir, args.module)
    if graph.get_node(args.node) is None:
        print(f"error: no node '{args.node}' in the graph for {args.product_dir}", file=sys.stderr)
        return 1

    impacted_ids = sorted(graph.downstream_impact(args.node))
    impacted_nodes = [graph.get_node(nid) for nid in impacted_ids]

    if args.json:
        print(
            json.dumps(
                {
                    "changed": args.node,
                    "impacted": [
                        {"id": n.id, "type": n.type, "label": n.label}
                        for n in impacted_nodes
                        if n is not None
                    ],
                },
                indent=2,
            )
        )
        return 0

    print(f"Change impact of {args.node}:")
    if not impacted_nodes:
        print("  (nothing transitively depends on this node)")
    for n in impacted_nodes:
        if n is not None:
            print(f"  - {_node_line(n)}")
    return 0


def _render_dot(graph: ckg.CKG) -> str:
    lines = ["digraph CKG {"]
    for node in graph.nodes.values():
        label = node.label.replace('"', "'") if node.label else node.id
        lines.append(f'  "{node.id}" [label="{node.id}\\n{label}"];')
    for edge in graph.edges:
        lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.type}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def _render_tree(graph: ckg.CKG) -> str:
    by_type: dict[str, list[ckg.Node]] = {}
    for node in graph.nodes.values():
        by_type.setdefault(node.type, []).append(node)

    lines = []
    for node_type in sorted(by_type):
        lines.append(f"{node_type}:")
        for node in sorted(by_type[node_type], key=lambda n: n.id):
            lines.append(f"  {_node_line(node)}")
    lines.append("\nEdges:")
    for edge in graph.edges:
        lines.append(f"  {edge.source} -{edge.type}-> {edge.target}")
    return "\n".join(lines) + "\n"


def _cmd_explore(args: argparse.Namespace) -> int:
    graph = ckg.build_graph(args.product_dir, args.module)
    if args.json:
        print(json.dumps(graph.to_dict(), indent=2))
    elif args.dot:
        print(_render_dot(graph), end="")
    else:
        print(_render_tree(graph), end="")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    graph = ckg.build_graph(args.product_dir, args.module)
    node = graph.get_node(args.node)
    if node is None:
        print(f"error: no node '{args.node}' in the graph for {args.product_dir}", file=sys.stderr)
        return 1

    print(_node_line(node))
    incoming = graph.edges_to(args.node)
    outgoing = graph.edges_from(args.node)
    print(f"\nIncoming edges ({len(incoming)}):")
    for e in incoming:
        print(f"  {e.source} -{e.type}-> {node.id}")
    print(f"\nOutgoing edges ({len(outgoing)}):")
    for e in outgoing:
        print(f"  {node.id} -{e.type}-> {e.target}")
    return 0


def _cmd_regenerate(args: argparse.Namespace) -> int:
    changed = [c.strip() for c in args.changed.split(",") if c.strip()]
    if not changed:
        print("error: --changed must list at least one node ID", file=sys.stderr)
        return 1

    graph_path = args.product_dir / "evidence" / "ckg.json"
    if graph_path.exists():
        graph = ckg.CKG.from_dict(json.loads(graph_path.read_text(encoding="utf-8")))
        stages = incremental.impacted_stages(graph, changed)
        if "requirements" in stages and not args.requirement:
            print(
                "error: this change set includes a Requirement-type node, "
                "which requires regenerating requirements/SRS.md via the "
                "LLM — pass --requirement with the (possibly updated) "
                "plain-language requirement text.",
                file=sys.stderr,
            )
            return 1

    spec = ProductSpec(
        name=args.module,
        plain_requirement=args.requirement or "",
        output_dir=args.product_dir,
        safety_class=args.safety_class,
        model=args.model,
    )
    executed = incremental.regenerate_from(spec, changed)
    print(f"Regenerated stages: {', '.join(executed)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query the Certification Knowledge Graph for a product.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    impact_parser = subparsers.add_parser(
        "impact", help="List nodes transitively affected if a given node changes"
    )
    _add_product_args(impact_parser)
    impact_parser.add_argument("--node", required=True, help="ID of the changed node, e.g. REQ-002")
    impact_parser.add_argument("--json", action="store_true")
    impact_parser.set_defaults(func=_cmd_impact)

    explore_parser = subparsers.add_parser("explore", help="Dump the full graph")
    _add_product_args(explore_parser)
    explore_parser.add_argument("--json", action="store_true")
    explore_parser.add_argument("--dot", action="store_true", help="Graphviz DOT output")
    explore_parser.set_defaults(func=_cmd_explore)

    show_parser = subparsers.add_parser("show", help="Show one node and all its edges")
    _add_product_args(show_parser)
    show_parser.add_argument("--node", required=True)
    show_parser.set_defaults(func=_cmd_show)

    regen_parser = subparsers.add_parser(
        "regenerate", help="Re-run only the pipeline stages downstream of changed node IDs"
    )
    _add_product_args(regen_parser)
    regen_parser.add_argument(
        "--changed", required=True, help="comma-separated changed node IDs, e.g. REQ-002,D-04"
    )
    regen_parser.add_argument(
        "--requirement",
        default=None,
        help="plain-language requirement text; required only if the change "
        "set includes a Requirement-type node",
    )
    regen_parser.add_argument("--safety-class", default="A")
    regen_parser.add_argument(
        "--model", default=os.environ.get("ORCHESTRATOR_MODEL", "claude-sonnet-5")
    )
    regen_parser.set_defaults(func=_cmd_regenerate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
