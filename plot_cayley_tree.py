"""2D neural Cayley tree matrix visualization (plot_cayley_tree.py).

Section 3.1 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Renders a balanced Cayley tree network mapped to the Section 6 variational
sorting zones (violet core / orange caustic rim / slate leaf field) with
concentric boundary horizons at r=0.35 and r=0.70.
"""

import os

import matplotlib

matplotlib.use("Agg")  # Run headless: no display required.
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


def generate_cayley_tree(z=3, generations=4, edge_length=1.0):
    """
    Generates nodes and edges for a balanced Cayley Tree network.
    z: coordination number of the root (subsequent nodes have z-1 children)
    """
    nodes = {0: (0.0, 0.0, 0)}  # id: (x, y, generation)
    edges = []
    current_id = 1

    # Track frontier nodes as tuples: (node_id, x, y, incoming_angle)
    frontier = []

    # Generation 1: Root branching
    for i in range(z):
        angle = (2 * np.pi * i) / z
        x = edge_length * np.cos(angle)
        y = edge_length * np.sin(angle)
        nodes[current_id] = (x, y, 1)
        edges.append((0, current_id))
        frontier.append((current_id, x, y, angle))
        current_id += 1

    # Subsequent generations
    for gen in range(2, generations + 1):
        next_frontier = []
        # Narrow the angular spreading to avoid parent/sibling overlap
        angle_spread = np.pi / (z ** (gen - 1))

        for parent_id, px, py, p_angle in frontier:
            # Each node has (z-1) children
            if z == 3:
                children_angles = [p_angle - angle_spread / 2, p_angle + angle_spread / 2]
            else:
                children_angles = np.linspace(p_angle - angle_spread,
                                              p_angle + angle_spread, z - 1)

            # Dynamic scaling factor to keep outer branches visually distinct
            gen_length = edge_length * (0.65 ** (gen - 1))

            for c_angle in children_angles:
                cx = px + gen_length * np.cos(c_angle)
                cy = py + gen_length * np.sin(c_angle)
                nodes[current_id] = (cx, cy, gen)
                edges.append((parent_id, current_id))
                next_frontier.append((current_id, cx, cy, c_angle))
                current_id += 1
        frontier = next_frontier

    return nodes, edges


def render_cayley_tree_matrix(output_path="config/cayley_tree_matrix.png",
                              z=3, generations=4, edge_length=1.2):
    """Renders the Cayley tree matrix mapped to the variational sorting zones."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # 1. Compute Pipeline Graph Configuration
    nodes, edges = generate_cayley_tree(z=z, generations=generations,
                                        edge_length=edge_length)

    # 2. Extract coordinates and normalize radial layout to match the Zone bounds
    coords = np.array([[data[0], data[1]] for data in nodes.values()])
    radii = np.sqrt(coords[:, 0] ** 2 + coords[:, 1] ** 2)
    max_radius = np.max(radii)
    normalized_radii = radii / max_radius  # Scale neatly from 0.0 to 1.0

    # 3. Setup Presentation Canvas Style
    fig, ax = plt.subplots(figsize=(8, 8), facecolor='#0B0F19')
    ax.set_facecolor('#0B0F19')

    # 4. Render Connection Lines (Quantum Links)
    for edge in edges:
        p1 = nodes[edge[0]]
        p2 = nodes[edge[1]]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#1E293B', linewidth=1.2, zorder=1)

    # 5. Segment and Plot Nodes by Structural Optimization Zones (Section 6).
    # Define styles to match the document's aesthetic.
    zone_colors = []
    node_sizes = []

    for r in normalized_radii:
        if r <= 0.35:
            zone_colors.append('#A855F7')  # Violet Core
            node_sizes.append(140)
        elif r <= 0.70:
            zone_colors.append('#F97316')  # Orange Caustic Rim
            node_sizes.append(80)
        else:
            zone_colors.append('#475569')  # Outer Muted Slate Field
            node_sizes.append(40)

    # Render Scatter Coordinates
    ax.scatter(coords[:, 0], coords[:, 1], c=zone_colors, s=node_sizes,
               zorder=2, edgecolors='#0B0F19', linewidths=0.5)

    # 6. Overlay Concordant Concentric Boundary Horizons
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(0.35 * max_radius * np.cos(theta), 0.35 * max_radius * np.sin(theta),
            color='#A855F7', linestyle=':', alpha=0.4, label='Zone 0 Bound (r=0.35)')
    ax.plot(0.70 * max_radius * np.cos(theta), 0.70 * max_radius * np.sin(theta),
            color='#F97316', linestyle=':', alpha=0.4, label='Zone 1 Bound (r=0.70)')

    # 7. Labels & Polish
    ax.set_title('Section 3.1: 2D Neural Cayley Tree Matrix\nMapped to Section 6 Variational Sorting Zones',
                 color='white', fontsize=12, fontweight='bold', pad=20)

    # Visual Legend Mapping
    legend_elements = [
        Line2D([0], [0], marker='o', color='#0B0F19', label='Zone 0: Core Synaptic Hub',
               markerfacecolor='#A855F7', markersize=10),
        Line2D([0], [0], marker='o', color='#0B0F19', label='Zone 1: Intermediate Caustic Rim',
               markerfacecolor='#F97316', markersize=8),
        Line2D([0], [0], marker='o', color='#0B0F19', label='Zone 2: Peripheral Leaf Layer',
               markerfacecolor='#475569', markersize=6),
    ]
    ax.legend(handles=legend_elements, loc='upper right', facecolor='#1E293B',
              edgecolor='#334155', labelcolor='white', fontsize=9)

    # Clean Graph Limits
    ax.set_xlim(-max_radius * 1.1, max_radius * 1.1)
    ax.set_ylim(-max_radius * 1.1, max_radius * 1.1)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Cayley tree matrix saved to '{output_path}' "
          f"({len(nodes)} nodes, {len(edges)} edges).")


if __name__ == "__main__":
    render_cayley_tree_matrix()
