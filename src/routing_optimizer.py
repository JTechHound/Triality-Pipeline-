"""Gradient-ascent throughput optimizer (src/routing_optimizer.py).

Module 7 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Variational path tuner. Employs finite-difference gradient ascent to tune
data routing coefficients to maximize global non-classical throughput.
"""

import numpy as np

from .routing import QCNNMultiHubRouter


class MultiTerminalRoutingOptimizer:
    def __init__(self, hubs_dictionary, lambda_scale=0.7):
        self.router = QCNNMultiHubRouter(hubs_dictionary, lambda_scale=lambda_scale)
        self.n_hubs = self.router.n_hubs
        self.names = self.router.hub_names
        np.random.seed(42)
        self.routing_weights = np.random.uniform(0.5, 1.0, (self.n_hubs, self.n_hubs))
        self.routing_weights = (self.routing_weights + self.routing_weights.T) / 2.0

    def compute_optimized_throughput(self, physical_noise):
        base_channels = self.router.route_compressed_network_channels(physical_noise)
        total_tp = 0.0
        for i in range(self.n_hubs):
            for j in range(i + 1, self.n_hubs):
                link = f"{self.names[i]} <---> {self.names[j]}"
                if link in base_channels:
                    total_tp += base_channels[link] * self.routing_weights[i, j]
        return total_tp

    def optimize_throughput_step(self, physical_noise, lr=0.05):
        eps = 1e-3
        gradients = np.zeros_like(self.routing_weights)
        for i in range(self.n_hubs):
            for j in range(i + 1, self.n_hubs):
                self.routing_weights[i, j] += eps
                self.routing_weights[j, i] += eps
                tp_plus = self.compute_optimized_throughput(physical_noise)
                self.routing_weights[i, j] -= 2 * eps
                self.routing_weights[j, i] -= 2 * eps
                tp_minus = self.compute_optimized_throughput(physical_noise)
                self.routing_weights[i, j] += eps
                self.routing_weights[j, i] += eps
                gradients[i, j] = (tp_plus - tp_minus) / (2 * eps)
                gradients[j, i] = gradients[i, j]
        self.routing_weights += lr * gradients
        self.routing_weights = np.clip(self.routing_weights, 0.1, 2.0)
