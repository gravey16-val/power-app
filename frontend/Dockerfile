# Frontend — single-stage image running the Vite dev server.
# Base image: node:20-slim (see DECISIONS.md for the deviation from
# ARCHITECTURE.md's node:20-alpine).
FROM node:20-slim

WORKDIR /app

# Backend URL — exposed as both a build arg and a runtime env var so that
# `import.meta.env.VITE_API_URL` resolves whether Vite runs as a dev server
# (reads the environment at runtime) or produces a production build (baked in).
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Install dependencies first to leverage Docker layer caching.
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the application source.
COPY . .

# Vite dev server port.
EXPOSE 5173

# Bind to 0.0.0.0 so the server is reachable from the host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
