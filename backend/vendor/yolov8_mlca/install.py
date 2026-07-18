"""Install MLCA into the active ultralytics package (run once after pip install ultralytics)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MLCA_SRC = ROOT / "mlca.py"


def _ensure_import(text: str) -> str:
    if "from ultralytics.nn.modules.mlca import MLCA, C2fMLCA" in text:
        return text
    anchor = "from ultralytics.nn.modules import ("
    insert = "from ultralytics.nn.modules.mlca import MLCA, C2fMLCA\n\nfrom ultralytics.nn.modules import ("
    if anchor not in text:
        raise RuntimeError("Cannot find import anchor in ultralytics/nn/tasks.py")
    return text.replace(anchor, insert, 1)


def _ensure_c2fmlca_sets(text: str) -> str:
    if "C2fMLCA," in text:
        return text
    text = text.replace(
        "            C2f,\n            C3k2,",
        "            C2f,\n            C2fMLCA,\n            C3k2,",
        1,
    )
    return text.replace(
        "            C2f,\n            C3k2,\n            C2fAttn,",
        "            C2f,\n            C2fMLCA,\n            C3k2,\n            C2fAttn,",
        1,
    )


def _ensure_mlca_args(text: str) -> str:
    if "elif m is MLCA:" in text:
        return text
    block = "        elif m is MLCA:\n            c2 = ch[f]\n            args = [ch[f], *args]\n"
    anchor = "        elif m in frozenset({TorchVision, Index}):"
    if anchor in text:
        return text.replace(anchor, block + anchor, 1)
    anchor2 = "        else:\n            c2 = ch[f]"
    if anchor2 in text:
        return text.replace(anchor2, block + anchor2, 1)
    raise RuntimeError("Cannot patch ultralytics/nn/tasks.py for MLCA")


def _patch_tasks(tasks_py: Path) -> None:
    text = tasks_py.read_text(encoding="utf-8")
    text = _ensure_import(text)
    text = _ensure_c2fmlca_sets(text)
    text = _ensure_mlca_args(text)

    if "C2fMLCA" not in text:
        raise RuntimeError("C2fMLCA not registered in tasks.py")
    if "elif m is MLCA:" not in text:
        raise RuntimeError("MLCA args patch missing in tasks.py")

    tasks_py.write_text(text, encoding="utf-8")
    print(f"Patched {tasks_py}")


def _patch_modules_init(init_py: Path) -> None:
    text = init_py.read_text(encoding="utf-8")
    if "from .mlca import MLCA, C2fMLCA" in text:
        print("modules/__init__.py already patched.")
        return
    anchor = "from .block import ("
    insert = "from .mlca import MLCA, C2fMLCA\n\nfrom .block import ("
    text = text.replace(anchor, insert, 1)
    if '"C2fMLCA"' not in text:
        text = text.replace('"C2f",\n', '"C2f",\n    "C2fMLCA",\n', 1)
        text = text.replace('"C2fAttn",\n', '"C2fAttn",\n    "MLCA",\n    "C2fMLCA",\n', 1)
    init_py.write_text(text, encoding="utf-8")
    print(f"Patched {init_py}")


def main() -> None:
    import ultralytics

    pkg = Path(ultralytics.__file__).resolve().parent
    modules_dir = pkg / "nn" / "modules"
    dst = modules_dir / "mlca.py"
    shutil.copy2(MLCA_SRC, dst)
    print(f"Copied MLCA module -> {dst}")

    _patch_modules_init(modules_dir / "__init__.py")
    _patch_tasks(pkg / "nn" / "tasks.py")
    print("YOLOv8 MLCA install complete.")


if __name__ == "__main__":
    main()
    sys.exit(0)
