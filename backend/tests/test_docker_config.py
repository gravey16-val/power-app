"""Docker build-context configuration tests (this ticket).

The backend image must build with the right env scoping:
- Runtime secrets (DATABASE_URL, CORS_ORIGINS) are injected at *run* time and
  must never be declared as build ARGs/ENVs, so they can't be baked into a
  layer.
- The .dockerignore must keep local secrets (.env) out of the build context
  while still shipping the files the build genuinely needs (requirements.txt).

These run inside the backend container, where the build context root is /app —
the parent of this tests/ directory — so the Dockerfile and .dockerignore that
were copied in at build time sit there.
"""

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent


def _instruction_lines(contents: str) -> list[str]:
    """Real instructions only — drop blank lines and `#` comments."""
    lines = []
    for raw in contents.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def test_dockerignore_excludes_env_but_keeps_required_build_files():
    entries = _instruction_lines((APP_ROOT / ".dockerignore").read_text())
    # Local secrets must never enter the build context...
    assert ".env" in entries
    # ...but files the build needs must remain available.
    for required in ("requirements.txt", "Dockerfile"):
        assert required not in entries


def test_dockerfile_does_not_bake_runtime_secrets():
    lines = _instruction_lines((APP_ROOT / "Dockerfile").read_text())
    dockerfile = "\n".join(lines)
    # Runtime configuration is supplied at run time; it must not appear in any
    # ARG/ENV instruction (which would bake it into an image layer).
    assert "ARG DATABASE_URL" not in dockerfile
    assert "ENV DATABASE_URL" not in dockerfile
    assert "ARG CORS_ORIGINS" not in dockerfile
    assert "ENV CORS_ORIGINS" not in dockerfile
