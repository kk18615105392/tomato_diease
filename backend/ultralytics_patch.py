"""将 MLCA / CBAM / PFA 自定义模块注册到当前环境的 ultralytics（E1–E11 推理必需）。"""

from __future__ import annotations

import sys
from pathlib import Path

VENDOR = Path(__file__).resolve().parent / "vendor" / "yolov8_mlca"
_patched = False


def ensure_ultralytics_custom(force: bool = False) -> None:
    """幂等安装：已注册则跳过。"""
    global _patched
    if not force and (_patched or custom_modules_ready()):
        _patched = True
        return

    if not VENDOR.is_dir():
        raise FileNotFoundError(
            f"缺少自定义 YOLOv8 模块目录: {VENDOR}\n"
            "请从 MLCA-master/yolov8_mlca 复制 mlca.py、attention_cbam.py、attention_pfa.py 及 install*.py"
        )

    vendor_str = str(VENDOR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

    from install import main as install_mlca
    from install_cbam import main as install_cbam
    from install_pfa import main as install_pfa

    install_mlca()
    install_cbam()
    install_pfa()
    _patched = True


def custom_modules_ready() -> bool:
    try:
        import ultralytics.nn.modules.attention_cbam  # noqa: F401
        import ultralytics.nn.modules.mlca  # noqa: F401
        import ultralytics.nn.modules.attention_pfa  # noqa: F401

        return True
    except ImportError:
        return False


if __name__ == "__main__":
    ensure_ultralytics_custom(force=True)
    print("custom_modules_ready:", custom_modules_ready())
