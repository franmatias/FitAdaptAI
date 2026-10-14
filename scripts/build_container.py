"""Construye sin recorrer cachés locales ni enviar secretos al motor Docker."""
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
files = [
    "Dockerfile", ".dockerignore", "package.json", "package-lock.json",
    "index.html", "vite.config.ts", "tailwind.config.js", "postcss.config.js",
    "requirements.txt", "api/__init__.py", "api/index.py", "api/demo.py",
    "deployment/container_app.py",
]
files += [p.name for p in root.glob("tsconfig*.json")]
files += [p.relative_to(root).as_posix() for p in (root / "src").rglob("*")
          if p.is_file() and p.suffix in {".ts", ".vue", ".css", ".json", ".svg", ".png", ".jpg", ".webp"}
          and not any(part.startswith(".") for part in p.relative_to(root).parts)]

with tempfile.TemporaryFile() as context:
    with tarfile.open(fileobj=context, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for name in sorted(set(files)):
            path = root / name
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise SystemExit(f"Ruta no permitida: {name}")
            archive.add(path, arcname=name, recursive=False)
    context.seek(0)
    result = subprocess.run(
        ["docker", "build", "--platform", "linux/amd64", "-t", "fitadaptai:local", "-"],
        stdin=context, cwd=root,
    )
    sys.exit(result.returncode)
