"""Register CBAM modules into active ultralytics (run once per env)."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CBAM_SRC = ROOT / "attention_cbam.py"

IMPORT_LINE = (
    "from ultralytics.nn.modules.attention_cbam import "
    "CBAM, CBAMv2, CBAMv2SA, CBAMv2T, C2fCBAM, C2fCBAMv2, C2fCBAMv2SA, C2fCBAMv2T"
)
INIT_IMPORT = (
    "from .attention_cbam import "
    "CBAM, CBAMv2, CBAMv2SA, CBAMv2T, C2fCBAM, C2fCBAMv2, C2fCBAMv2SA, C2fCBAMv2T"
)

C2F_CBAM_CLASSES = ("C2fCBAM", "C2fCBAMv2", "C2fCBAMv2SA", "C2fCBAMv2T")
STANDALONE = ("CBAM", "CBAMv2", "CBAMv2SA", "CBAMv2T")


def _ensure_import(text: str) -> str:
    if "from ultralytics.nn.modules.attention_cbam import" in text:
        text = re.sub(
            r"from ultralytics\.nn\.modules\.attention_cbam import[^\n]+\n",
            IMPORT_LINE + "\n",
            text,
        )
        return text
    anchor = "from ultralytics.nn.modules import ("
    insert = IMPORT_LINE + "\n\nfrom ultralytics.nn.modules import ("
    if anchor not in text:
        raise RuntimeError("Cannot find import anchor in tasks.py")
    return text.replace(anchor, insert, 1)


def _ensure_in_frozenset(text: str, block_name: str, class_names: tuple[str, ...]) -> str:
    """Add class names to base_modules or repeat_modules frozenset if missing."""
    m = re.search(rf"{block_name}\s*=\s*frozenset\(\s*\{{", text)
    if not m:
        return text
    start = m.end()
    end = text.find("}", start)
    block = text[start:end]
    for cls in class_names:
        if f"{cls}," not in block and f"{cls}\n" not in block:
            anchor = "            C2f,\n"
            if anchor in block:
                block = block.replace(anchor, anchor + f"            {cls},\n", 1)
            elif "            C2fMLCA,\n" in block:
                block = block.replace(
                    "            C2fMLCA,\n",
                    f"            C2fMLCA,\n            {cls},\n",
                    1,
                )
            else:
                block = f"            {cls},\n" + block
    return text[:start] + block + text[end:]


def _ensure_standalone_args(text: str) -> str:
    blocks = []
    for name in STANDALONE:
        if f"elif m is {name}:" in text:
            continue
        blocks.append(
            f"        elif m is {name}:\n            c2 = ch[f]\n            args = [ch[f], *args]\n"
        )
    if not blocks:
        return text
    patch = "".join(blocks)
    anchor = "        elif m in frozenset({TorchVision, Index}):"
    if anchor in text:
        return text.replace(anchor, patch + anchor, 1)
    if "        elif m is MLCA:" in text:
        return text.replace(
            "        elif m is MLCA:\n            c2 = ch[f]\n            args = [ch[f], *args]\n",
            "        elif m is MLCA:\n            c2 = ch[f]\n            args = [ch[f], *args]\n" + patch,
            1,
        )
    anchor2 = "        else:\n            c2 = ch[f]"
    return text.replace(anchor2, patch + anchor2, 1)


def _patch_modules_init(init_py: Path) -> None:
    text = init_py.read_text(encoding="utf-8")
    if "from .attention_cbam import" in text:
        text = re.sub(
            r"from \.attention_cbam import[^\n]+\n",
            INIT_IMPORT + "\n",
            text,
        )
    else:
        text = text.replace("from .block import (", INIT_IMPORT + "\n\nfrom .block import (", 1)
    for name in (*C2F_CBAM_CLASSES, *STANDALONE):
        if f'"{name}"' not in text:
            text = text.replace('"C2fMLCA",\n', f'"C2fMLCA",\n    "{name}",\n', 1)
    init_py.write_text(text, encoding="utf-8")
    print(f"Patched {init_py}")


def main() -> None:
    import ultralytics

    pkg = Path(ultralytics.__file__).resolve().parent
    modules_dir = pkg / "nn" / "modules"
    dst = modules_dir / "attention_cbam.py"
    shutil.copy2(CBAM_SRC, dst)
    print(f"Copied CBAM module -> {dst}")

    _patch_modules_init(modules_dir / "__init__.py")
    tasks_py = pkg / "nn" / "tasks.py"
    text = tasks_py.read_text(encoding="utf-8")
    text = _ensure_import(text)
    text = _ensure_in_frozenset(text, "base_modules", C2F_CBAM_CLASSES)
    text = _ensure_in_frozenset(text, "repeat_modules", C2F_CBAM_CLASSES)
    text = _ensure_standalone_args(text)
    tasks_py.write_text(text, encoding="utf-8")
    print(f"Patched {tasks_py}")
    print("YOLOv8 CBAM install complete.")


if __name__ == "__main__":
    main()
    sys.exit(0)
