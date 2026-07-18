"""PFA (Parallel Fusion Attention) for YOLOv8 — inspired by YOLOv8n-PFA (2026).

CBAM applies channel then spatial **in series**, which can over-suppress weak
target features. PFA runs both branches **in parallel** on the same input,
learnably fuses them, then refines with lightweight DWConv.
Placement: after SPPF (deep semantic features).
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn


def _safe_ratio(c: int, ratio: int = 16) -> int:
    while c // ratio < 1 and ratio > 1:
        ratio //= 2
    return max(ratio, 1)


class _ChannelAtt(nn.Module):
    def __init__(self, c: int, ratio: int = 16):
        super().__init__()
        ratio = _safe_ratio(c, ratio)
        hidden = max(c // ratio, 1)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.mlp = nn.Sequential(
            nn.Conv2d(c, hidden, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, c, 1, bias=False),
        )
        self.act = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.mlp(self.pool(x)))


class _SpatialAtt(nn.Module):
    def __init__(self, kernel_size: int = 7):
        super().__init__()
        p = kernel_size // 2
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=p, bias=False)
        self.act = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg = torch.mean(x, dim=1, keepdim=True)
        mx, _ = torch.max(x, dim=1, keepdim=True)
        return self.act(self.conv(torch.cat([avg, mx], dim=1)))


class PFA(nn.Module):
    """Parallel Fusion Attention block (standalone, after SPPF).

    forward: parallel channel & spatial gates → weighted fusion → DWConv residual.
    """

    def __init__(self, c1: int, ratio: int = 16, spatial_k: int = 7):
        super().__init__()
        self.channel = _ChannelAtt(c1, ratio)
        self.spatial = _SpatialAtt(spatial_k)
        self.fuse = nn.Parameter(torch.zeros(2))
        self.dw = nn.Sequential(
            nn.Conv2d(c1, c1, 3, padding=1, groups=c1, bias=False),
            nn.BatchNorm2d(c1),
            nn.SiLU(inplace=True),
            nn.Conv2d(c1, c1, 1, bias=False),
            nn.BatchNorm2d(c1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = torch.softmax(self.fuse, dim=0)
        xc = x * self.channel(x)
        xs = x * self.spatial(x)
        out = w[0] * xc + w[1] * xs
        return out + self.dw(out)
