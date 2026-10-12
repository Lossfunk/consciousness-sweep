#!/usr/bin/env python3
"""Set up the portable sweep repository. Never invokes a model or starts a run."""
import argparse
from pathlib import Path
import subprocess
import sys
import venv


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", default=".venv", help="Isolated dependency environment")
    parser.add_argument("--no-install", action="store_true", help="Reuse installed dependencies without network access")
    parser.add_argument("--verify-only", action="store_true", help="Verify distribution without installing or probing the host")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 9):
        parser.error("Python 3.9 or newer is required")
    root = Path(__file__).resolve().parent
    if (root / "DISTRIBUTION_MANIFEST.json").exists():
        from sweep.distribution import verify
        result = verify(root)
        print("Verified %d immutable distribution files." % result["files_verified"])
    elif args.verify_only:
        parser.error("No distribution manifest; build a clean distribution first")
    if args.verify_only:
        return 0
    # Empty directory scaffolds cannot survive a Git checkout. Recreate only
    # containers required by the unchanged native package's preflight.
    if (root / "science" / "RELEASE_MANIFEST.json").is_file():
        for relative in ("runs", "outputs/consolidated"):
            (root / "science" / relative).mkdir(parents=True, exist_ok=True)
    environment = Path(args.venv)
    if not environment.is_absolute():
        environment = root / environment
    executable = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not executable.exists():
        if args.no_install:
            parser.error("The selected environment is absent; omit --no-install to create it")
        venv.EnvBuilder(with_pip=True).create(str(environment))
    requirements = root / "requirements.txt"
    if (root / "packaging" / "requirements.txt").is_file():
        requirements = root / "packaging" / "requirements.txt"
    if not args.no_install:
        subprocess.run([str(executable), "-m", "pip", "install", "-r", str(requirements)], cwd=str(root), check=True)
    subprocess.run([str(executable), "-B", "-m", "sweep", "doctor"], cwd=str(root), check=True)
    print("Setup complete. Start your agent in this directory and ask it to follow AGENTS.md.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, subprocess.CalledProcessError) as error:
        print("Setup stopped: " + str(error), file=sys.stderr)
        raise SystemExit(1)
