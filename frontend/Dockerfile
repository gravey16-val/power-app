# Single-stage image (project rule: no multi-stage builds).
FROM node:20-alpine

WORKDIR /app

# Copy the manifest *and* the committed lockfile, then install with `npm ci`.
# `npm ci` installs strictly from package-lock.json: it is deterministic and
# avoids the dependency-tree resolution that `npm install` performs, so the
# build is reproducible and does not stall on registry metadata.
# (See DECISIONS.md — the M1 scaffold used `npm install` only until the lock
# file was committed; it now is.)
COPY package.json package-lock.json ./
RUN npm ci

# `.dockerignore` excludes node_modules from this COPY, so a host-built
# node_modules cannot overwrite the platform-correct deps installed above —
# the root cause of the build failing at this step (ticket #83).
COPY . .

EXPOSE 5173

# Vite dev server, bound to 0.0.0.0 so it is reachable from the host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
