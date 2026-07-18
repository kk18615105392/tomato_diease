"""MLCA module for Ultralytics YOLOv8 (paper-aligned implementation)."""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from ultralytics.nn.modules.block import C2f


class MLCA(nn.Module):
    """Mixed Local Channel Attention.

    GAP + LAP(ks×ks) dual branch, Conv1d channel interaction, direct add, Sigmoid gate.
    """

    def __init__(self, c1: int, local_size: int = 5, b: int = 1):
        super().__init__()
        self.local_size = local_size
        self.b = b
        k = self._adapt_kernel(c1, b)

        self.conv = nn.Conv1d(1, 1, kernel_size=k, padding=(k - 1) // 2, bias=False)
        self.conv_local = nn.Conv1d(1, 1, kernel_size=k, padding=(k - 1) // 2, bias=False)
        self.local_arv_pool = nn.AdaptiveAvgPool2d(local_size)
        self.global_arv_pool = nn.AdaptiveAvgPool2d(1)

    @staticmethod
    def _adapt_kernel(c: int, b: int = 1) -> int:
        t = int(abs(math.log2(max(c, 2)) / 2 + b / 2))
        t = max(t, 1)
        return t if t % 2 else t + 1

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, m, n = x.shape

        local_arv = self.local_arv_pool(x)
        global_arv = self.global_arv_pool(x)

        temp_local = local_arv.view(b, c, -1).transpose(-1, -2).reshape(b, 1, -1)
        y_local = self.conv_local(temp_local)
        y_local = y_local.reshape(b, self.local_size * self.local_size, c).transpose(-1, -2)
        y_local = y_local.view(b, c, self.local_size, self.local_size)

        temp_global = global_arv.view(b, c, -1).transpose(-1, -2)
        y_global = self.conv(temp_global).view(b, c, 1, 1)

        feat_local = F.interpolate(y_local, size=(m, n), mode="nearest")
        feat_global = F.interpolate(y_global, size=(m, n), mode="nearest")

        att = torch.sigmoid(feat_local + feat_global)
        return x * att


class C2fMLCA(C2f):
    """C2f block with MLCA applied on the output feature map."""

    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        self.mlca = MLCA(c2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.mlca(super().forward(x))
