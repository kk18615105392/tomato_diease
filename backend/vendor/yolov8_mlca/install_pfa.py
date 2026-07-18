"""Register PFA module into active ultralytics."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PFA_SRC = ROOT / "attention_pfa.py"

IMPORT_LINE = "from ultralytics.nn.modules.attention_pfa import PFA"
INIT_IMPORT = "from .attention_pfa import PFA"
STANDALONE = ("PFA",)


def _ensure_import(text: str) -> str:
    if "from ultralytics.nn.modules.attention_pfa import" in text:
        text = re.sub(
            r"from ultralytics\.nn\.modules\.attention_pfa import[^\n]+\n",
            IMPORT_LINE + "\n",
            text,
        )
        return text
    anchor = "from ultralytics.nn.modules import ("
    insert = IMPORT_LINE + "\n\nfrom ultralytics.nn.modules import ("
    if anchor not in text:
        raise RuntimeError("Cannot find import anchor in tasks.py")
    return text.replace(anchor, insert, 1)


def _ensure_standalone_args(text: str) -> str:
    if "elif m is PFA:" in text:
        return text
    block = "        elif m is PFA:\n            c2 = ch[f]\n            args = [ch[f], *args]\n"
    anchor = "        elif m in frozenset({TorchVision, Index}):"
    if anchor in text:
        return text.replace(anchor, block + anchor, 1)
    if "        elif m is MLCA:" in text:
        return text.replace(
            "        elif m is MLCA:\n            c2 = ch[f]\n            args = [ch[f], *args]\n",
            "        elif m is MLCA:\n            c2 = ch[f]\n            args = [ch[f], *args]\n" + block,
            1,
        )
    anchor2 = "        else:\n            c2 = ch[f]"
    return text.replace(anchor2, block + anchor2, 1)


def _patch_modules_init(init_py: Path) -> None:
    text = init_py.read_text(encoding="utf-8")
    if "from .attention_pfa import" in text:
        text = re.sub(r"from \.attention_pfa import[^\n]+\n", INIT_IMPORT + "\n", text)
    else:
        text = text.replace("from .block import (", INIT_IMPORT + "\n\nfrom .block import (", 1)
    if '"PFA"' not in text:
        text = text.replace('"MLCA",\n', '"MLCA",\n    "PFA",\n', 1)
    init_py.write_text(text, encoding="utf-8")
    print(f"Patched {init_py}")


def main() -> None:
    import ultralytics

    pkg = Path(ultralytics.__file__).resolve().parent
    modules_dir = pkg / "nn" / "modules"
    dst = modules_dir / "attention_pfa.py"
    shutil.copy2(PFA_SRC, dst)
    print(f"Copied PFA module -> {dst}")

    _patch_modules_init(modules_dir / "__init__.py")
    tasks_py = pkg / "nn" / "tasks.py"
    text = tasks_py.read_text(encoding="utf-8")
    text = _ensure_import(text)
    text = _ensure_standalone_args(text)
    tasks_py.write_text(text, encoding="utf-8")
    print(f"Patched {tasks_py}")
    print("YOLOv8 PFA install complete.")


if __name__ == "__main__":
    main()
    sys.exit(0)
