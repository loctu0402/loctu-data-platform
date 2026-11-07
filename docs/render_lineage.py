import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "dbt" / "target" / "manifest.json"
OUT = ROOT / "docs" / "lineage.svg"

LAYERS = [
    ("bronze", "Bronze · sources", "#f59e0b"),
    ("staging", "Silver · staging", "#38bdf8"),
    ("intermediate", "Silver · intermediate", "#818cf8"),
    ("gold", "Gold · contracted marts", "#facc15"),
    ("exposure", "Consumers", "#34d399"),
]
COL_W, ROW_H, BOX_W, BOX_H, TOP, LEFT = 262, 44, 214, 30, 92, 28


def layer_of(node):
    if node["resource_type"] == "source":
        return "bronze"
    if node["resource_type"] == "exposure":
        return "exposure"
    fqn = node["fqn"]
    if "gold" in fqn:
        return "gold"
    if node["name"].startswith(("int_", "util_")):
        return "intermediate"
    return "staging"


def label_of(node):
    if node["resource_type"] == "source":
        return f"{node['source_name']}.{node['name']}"
    return node.get("label") or node["name"]


def main():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    nodes = {k: v for k, v in {**m["nodes"], **m["sources"], **m["exposures"]}.items() if v["resource_type"] in ("model", "source", "exposure")}
    columns = {key: sorted((k for k, v in nodes.items() if layer_of(v) == key), key=lambda k: (k.split(".")[-2] if nodes[k]["resource_type"] == "source" else "", nodes[k]["name"])) for key, _, _ in LAYERS}
    pos, row = {}, {}
    for ci, (key, _, _) in enumerate(LAYERS):
        if ci:
            def centre(k):
                rows = [row[p] for p in nodes[k].get("depends_on", {}).get("nodes", []) if p in row]
                return sum(rows) / len(rows) if rows else 0
            columns[key] = sorted(columns[key], key=centre)
        for ri, k in enumerate(columns[key]):
            pos[k], row[k] = (LEFT + ci * COL_W, TOP + ri * ROW_H), ri
    height = TOP + max(len(v) for v in columns.values()) * ROW_H + 30
    width = LEFT * 2 + COL_W * (len(LAYERS) - 1) + BOX_W
    colour = {key: c for key, _, c in LAYERS}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="Inter, Segoe UI, Arial, sans-serif">',
        f'<rect width="{width}" height="{height}" rx="16" fill="#0b1220"/>',
        f'<text x="{LEFT}" y="38" fill="#e2e8f0" font-size="18" font-weight="700">dbt lineage</text>',
        f'<text x="{LEFT}" y="58" fill="#94a3b8" font-size="12">Generated from dbt/target/manifest.json by docs/render_lineage.py</text>',
    ]
    for ci, (key, title, c) in enumerate(LAYERS):
        parts.append(f'<text x="{LEFT + ci * COL_W}" y="{TOP - 14}" fill="{c}" font-size="12" font-weight="700" letter-spacing="0.06em">{escape(title.upper())}</text>')
    edge_id = 0
    for k, node in nodes.items():
        for parent in node.get("depends_on", {}).get("nodes", []):
            if parent not in pos or k not in pos:
                continue
            (x1, y1), (x2, y2) = pos[parent], pos[k]
            sx, sy, ex, ey = x1 + BOX_W, y1 + BOX_H / 2, x2, y2 + BOX_H / 2
            mid = (sx + ex) / 2
            d = f"M{sx},{sy} C{mid},{sy} {mid},{ey} {ex},{ey}"
            c = colour[layer_of(nodes[parent])]
            parts.append(f'<path id="e{edge_id}" d="{d}" fill="none" stroke="{c}" stroke-opacity="0.35" stroke-width="1.4"/>')
            dur = 2.6 + (edge_id % 5) * 0.4
            parts.append(f'<circle r="2.6" fill="{c}"><animateMotion dur="{dur}s" repeatCount="indefinite" begin="{(edge_id % 7) * 0.35}s"><mpath href="#e{edge_id}"/></animateMotion></circle>')
            edge_id += 1
    for k, (x, y) in pos.items():
        c = colour[layer_of(nodes[k])]
        parts.append(f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="7" fill="#111a2e" stroke="{c}" stroke-width="1.2"/>')
        parts.append(f'<text x="{x + 10}" y="{y + 19.5}" fill="#e2e8f0" font-size="11.5">{escape(label_of(nodes[k]))}</text>')
    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(pos)} nodes, {edge_id} edges")


if __name__ == "__main__":
    main()
