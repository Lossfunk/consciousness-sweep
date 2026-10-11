#!/usr/bin/env python3
"""Create the repository's canonical virtual environment from pinned requirements."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def main() -> int:
    if sys.version_info < (3, 9) or os.name != "posix":
        raise SystemExit("supported runtime requires Python >=3.9 on a POSIX Unix environment")
    parser = argparse.ArgumentParser()
    parser.add_argument("--venv", type=Path, default=Path(".venv"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    target = args.venv if args.venv.is_absolute() else root / args.venv
    target = target.resolve()
    if target == root or root not in target.parents:
        raise SystemExit("refusing bootstrap: --venv must be a dedicated directory inside the repository")
    requirements = root / "requirements.txt"
    if not requirements.is_file():
        raise SystemExit(f"missing requirements file: {requirements}")
    python = venv_python(target)
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(target)
    try:
        subprocess.run(
            [str(python), "-m", "pip", "install", "--requirement", str(requirements)],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [str(python), "-c", "import yaml, jsonschema; print('PASS: pinned dependencies import')"],
            cwd=root,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"bootstrap failed (exit {exc.returncode}); the partial environment is safe to rerun "
            "after resolving package-index/network access"
        ) from None
    print(f"PASS: canonical environment ready at {target}")
    print(f"Use: {python} tools/preflight.py --mode registered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
