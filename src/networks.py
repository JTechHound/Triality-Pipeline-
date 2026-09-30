"""High-dimensional spatial graphs (src/networks.py).

Module 3 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Handles many-body state tracking across networks. Executes partial trace
operations to isolate local subsets and extract Von Neumann state entropy.
"""

import numpy as np


class NonEquilibriumNetwork:
    def __init__(self, n_nodes=4):
        self.n_nodes = n_nodes
        self.dim = 2 ** n_nodes

    def extract_bipartite_subspace(self, rho, index_a, index_b):
        """Traces out peripheral coordinates to isolate a target 4x4 density block.

        NOTE: Corrected from the source document. The document indexed the ket
        axes as ``self.n_nodes + idx`` on every iteration, but each partial trace
        shrinks the tensor by two axes, so later iterations indexed out of bounds
        and the method crashed. The ket-axis offset now tracks the number of
        remaining node pairs, preserving the intended trace-out order.
        """
        tensor_shape = [2] * (2 * self.n_nodes)
        rho_tensor = rho.reshape(tensor_shape)
        all_indices = set(range(self.n_nodes))
        trace_out = sorted(list(all_indices - {index_a, index_b}), reverse=True)
        pairs = self.n_nodes
        for idx in trace_out:
            rho_tensor = np.trace(rho_tensor, axis1=idx, axis2=pairs + idx)
            pairs -= 1
        return rho_tensor.reshape(4, 4)

    def calculate_von_neumann_entropy(self, rho_sub):
        """Calculates local Von Neumann entropy for structural state evaluations."""
        evals = np.linalg.eigvalsh(rho_sub)
        evals = np.clip(evals, 1e-15, None)
        return -np.sum(evals * np.log2(evals))
