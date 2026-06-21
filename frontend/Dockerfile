# Single-stage image (no multi-stage build/production split — project convention).
# Base image pinned to a patch version for reproducible builds.
FROM node:20.18-alpine

WORKDIR /app

# Install dependencies first to leverage Docker layer caching.
# `npm install` (not `npm ci`) because the scaffold ships without a committed
# lockfile yet; the lockfile is generated on first build.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Vite dev server, bound to 0.0.0.0 so it is reachable from the host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
