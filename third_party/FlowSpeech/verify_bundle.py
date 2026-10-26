"""Build a review-only bundle and rerun offline tests against extracted runtime files."""

import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "flowspeech_v1.py",
    "flowspeech_notebook.py",
    "claude_directed_narration.ipynb",
    "requirements.txt",
    "README.md",
    "CHANGELOG.md",
]
TESTS = "tests"
NAME = "flowspeech-v1-cookbook-review.tar.gz"


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / NAME
    pattern = re.compile(
        rb"(?:gh[pousr]_[A-Za-z0-9]{25,}|npm_[A-Za-z0-9]{25,}|"
        rb"pypi-[A-Za-z0-9_-]{40,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
    )
    with archive.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as bundle:
            for name in sorted(FILES):
                path = ROOT / name
                if path.is_symlink():
                    raise RuntimeError("Symlinks are not allowed in the bundle")
                content = path.read_bytes()
                if pattern.search(content):
                    raise RuntimeError(f"Secret-like content in {name}")
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(content), 0o644
                bundle.addfile(info, io.BytesIO(content))
    temporary = ROOT / ".test-tmp"
    temporary.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bundle-", dir=temporary) as directory:
        extracted = Path(directory)
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            if sorted(member.name for member in members) != sorted(FILES):
                raise RuntimeError("Unexpected bundle file inventory")
            for member in members:
                if not member.isfile() or member.name not in FILES:
                    raise RuntimeError("Unexpected archive member")
                content = bundle.extractfile(member).read()
                if content != (ROOT / member.name).read_bytes():
                    raise RuntimeError("Bundled file differs from source")
                (extracted / member.name).write_bytes(content)
        env = dict(
            os.environ,
            FLOWSPEECH_TEST_ROOT=str(extracted),
            PYTHONDONTWRITEBYTECODE="1",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        )
        subprocess.run(  # noqa: S603 - fixed interpreter and local offline test paths
            [
                sys.executable,
                "-m",
                "pytest",
                str(ROOT / TESTS),
                f"--confcutdir={ROOT / TESTS}",
                "-p",
                "no:cacheprovider",
                f"--basetemp={extracted / 'test-temp'}",
                "-q",
            ],
            env=env,
            check=True,
        )
    print(
        json.dumps(
            {
                "archive": str(archive),
                "files": sorted(FILES),
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "source_matches": True,
                "secret_scan": "passed",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
