"""CBAM attention for Ultralytics YOLOv8 (replacement / comparison vs MLCA).

Variants:
  CBAM / C2fCBAM       — E7a 原版顺序 (Channel→Spatial, k=7), 4层+SPPF后
  CBAMv2 / C2fCBAMv2  — E7c/E7d 可配置顺序、核大小、ECA、残差门控
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn

from ultralytics.nn.modules.block import C2f


def _safe_ratio(c: int, ratio: int = 16) -> int:
    """Avoid zero bottleneck channels on small width (yolov8n)."""
    while c // ratio < 1 and ratio > 1:
        ratio //= 2
    return max(ratio, 1)


class ChannelAttention(nn.Module):
    def __init__(self, c: int, ratio: int = 16):
        super().__init__()
        ratio = _safe_ratio(c, ratio)
        hidden = max(c // ratio, 1)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.mlp = nn.Sequential(
            nn.Conv2d(c, hidden, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, c, 1, bias=False),
        )
        self.act = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.mlp(self.avg_pool(x)) + self.mlp(self.max_pool(x)))


class ECAChannelAttention(nn.Module):
    """Lightweight ECA-style channel attention (Wang et al.)."""

    def __init__(self, c: int, gamma: int = 2, b: int = 1):
        super().__init__()
        t = int(abs(math.log2(max(c, 2)) / gamma + b / gamma))
        k = t if t % 2 else t + 1
        k = max(3, k)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k, padding=k // 2, bias=False)
        self.act = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.avg_pool(x).squeeze(-1).transpose(-1, -2)
        y = self.conv(y).transpose(-1, -2).unsqueeze(-1)
        return self.act(y)


class SpatialAttention(nn.Module):
    def __init__(self, kernel_size: int = 7):
        super().__init__()
        padding = kernel_size // 2
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
        self.act = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg = torch.mean(x, dim=1, keepdim=True)
        mx, _ = torch.max(x, dim=1, keepdim=True)
        return self.act(self.conv(torch.cat([avg, mx], dim=1)))


class CBAM(nn.Module):
    """Standalone CBAM block (E7a: Channel→Spatial, k=7)."""

    def __init__(self, c1: int, ratio: int = 16, kernel_size: int = 7):
        super().__init__()
        self.channel = ChannelAttention(c1, ratio)
        self.spatial = SpatialAttention(kernel_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x * self.channel(x)
        x = x * self.spatial(x)
        return x


class CBAMv2(nn.Module):
    """Improved CBAM for small-target detection (E7c/E7d).

    Args:
        c1: input channels
        kernel_size: spatial conv kernel (3 for small lesions, 7 for semantic layers)
        spatial_first: True → Spatial→Channel (better for localization)
        ratio: MLP bottleneck ratio for channel attention
        residual: residual gating x + β·(x·att - x)
        beta: initial residual scale (learnable when residual=True)
        use_eca: use ECA instead of avg+max MLP for channel attention
    """

    def __init__(
        self,
        c1: int,
        kernel_size: int = 7,
        spatial_first: bool = False,
        ratio: int = 16,
        residual: bool = True,
        beta: float = 0.1,
        use_eca: bool = False,
    ):
        super().__init__()
        self.spatial_first = spatial_first
        self.residual = residual
        if residual:
            self.beta = nn.Parameter(torch.tensor(float(beta)))
        channel_cls = ECAChannelAttention if use_eca else ChannelAttention
        self.channel = channel_cls(c1, ratio) if not use_eca else channel_cls(c1)
        self.spatial = SpatialAttention(kernel_size)

    def _gate(self, x: torch.Tensor, att: torch.Tensor) -> torch.Tensor:
        if self.residual:
            return x + self.beta * (x * att - x)
        return x * att

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.spatial_first:
            x = self._gate(x, self.spatial(x))
            x = self._gate(x, self.channel(x))
        else:
            x = self._gate(x, self.channel(x))
            x = self._gate(x, self.spatial(x))
        return x


class C2fCBAM(C2f):
    """C2f with CBAM on output features (E7a full-stack placement)."""

    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        self.cbam = CBAM(c2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.cbam(super().forward(x))


class C2fCBAMv2(C2f):
    """C2f with configurable CBAMv2 on output."""

    def __init__(
        self,
        c1: int,
        c2: int,
        n: int = 1,
        shortcut: bool = False,
        g: int = 1,
        e: float = 0.5,
        kernel_size: int = 7,
        spatial_first: bool = False,
        ratio: int = 16,
        residual: bool = True,
        beta: float = 0.1,
        use_eca: bool = False,
    ):
        super().__init__(c1, c2, n, shortcut, g, e)
        self.cbam = CBAMv2(
            c2,
            kernel_size=kernel_size,
            spatial_first=spatial_first,
            ratio=ratio,
            residual=residual,
            beta=beta,
            use_eca=use_eca,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.cbam(super().forward(x))


class C2fCBAMv2SA(C2fCBAMv2):
    """E7c preset: Spatial→Channel, k=3, MLP channel, residual."""

    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5):
        super().__init__(c1, c2, n, shortcut, g, e, kernel_size=3, spatial_first=True, use_eca=False)


class C2fCBAMv2T(C2fCBAMv2):
    """E7d preset: Spatial→Channel, k=3, ECA, residual (tomato small-target)."""

    def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5):
        super().__init__(c1, c2, n, shortcut, g, e, kernel_size=3, spatial_first=True, use_eca=True)


class CBAMv2SA(CBAMv2):
    """E7c preset after SPPF: SA-first k=3."""

    def __init__(self, c1: int):
        super().__init__(c1, kernel_size=3, spatial_first=True, use_eca=False)


class CBAMv2T(CBAMv2):
    """E7d preset after SPPF: SA-first k=7, ECA, residual."""

    def __init__(self, c1: int):
        super().__init__(c1, kernel_size=7, spatial_first=True, use_eca=True)
