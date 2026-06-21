# docker-bake.hcl — build-time configuration for the full stack.
#
# `docker buildx bake` builds the same images as `docker compose build`, but it
# is the canonical place to declare *build args* explicitly so a bake build does
# not silently fall back to defaults (the failure mode behind this ticket).
#
# Scope rule: only NON-SECRET, build-time configuration belongs here. The
# backend's runtime configuration (DATABASE_URL, CORS_ORIGINS) is injected at
# *run* time and is deliberately never a build arg, so secrets can never be
# baked into an image layer.
#
# Usage:
#   docker buildx bake                       # build both targets
#   VITE_API_URL=https://api.example.com docker buildx bake frontend
#   docker buildx bake --print               # inspect the resolved config

variable "VITE_API_URL" {
  # Base URL the browser uses to reach the FastAPI backend. Public (not a
  # secret) and inlined into the static frontend bundle by Vite at build time.
  # Defaults to the local backend so a bare `docker buildx bake` works offline.
  default = "http://localhost:8000"
}

group "default" {
  targets = ["backend", "frontend"]
}

target "backend" {
  context    = "./backend"
  dockerfile = "Dockerfile"
  # No build args: the backend needs no build-time configuration. Its runtime
  # secrets (DATABASE_URL, CORS_ORIGINS) are supplied at run time and must never
  # be baked into the image.
}

target "frontend" {
  context    = "./frontend"
  dockerfile = "Dockerfile"
  args = {
    # Forwarded to the frontend Dockerfile's `ARG VITE_API_URL`.
    VITE_API_URL = "${VITE_API_URL}"
  }
}
