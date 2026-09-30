"""Dijkstra multi-hop relay protocol (src/relay_routing.py).

Module 6 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Dynamically diverts data tracks around high-noise spatial regions.
Choked line-of-sight paths (>5.0% noise) are assigned infinite routing penalties.
"""

import numpy as np


class MultiHopRelayRouter:
    def __init__(self, node_positions, connectivity_matrix):
        self.positions = np.array(node_positions)
        self.capacities = np.array(connectivity_matrix)
        self.n_nodes = len(node_positions)

    def compute_noise_attenuated_costs(self, global_noise_map):
        cost_matrix = np.zeros((self.n_nodes, self.n_nodes))
        for i in range(self.n_nodes):
            for j in range(self.n_nodes):
                if i == j:
                    continue
                # Penalize paths exceeding the 5.0% threshold limit
                if global_noise_map[i, j] > 0.050:
                    cost_matrix[i, j] = float('inf')
                else:
                    cost_matrix[i, j] = 1.0 / (self.capacities[i, j] + 1e-6)
        return cost_matrix

    def execute_relay_path(self, source, target, cost_matrix):
        unvisited = set(range(self.n_nodes))
        distances = {n: float('inf') for n in range(self.n_nodes)}
        previous = {n: None for n in range(self.n_nodes)}
        distances[source] = 0.0
        while unvisited:
            curr = min(unvisited, key=lambda n: distances[n])
            if distances[curr] == float('inf') or curr == target:
                break
            unvisited.remove(curr)
            for nxt in range(self.n_nodes):
                if nxt in unvisited:
                    tentative = distances[curr] + cost_matrix[curr, nxt]
                    if tentative < distances[nxt]:
                        distances[nxt] = tentative
                        previous[nxt] = curr
        path, c = [], target
        while c is not None:
            path.insert(0, c)
            c = previous[c]
        return path if path[0] == source else []
