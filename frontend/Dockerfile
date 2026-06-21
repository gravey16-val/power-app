# Single-stage image (project rule: no multi-stage builds).
FROM node:20-alpine

WORKDIR /app

# VITE_API_URL is a *build-time* value: Vite inlines `import.meta.env.VITE_*`
# into the bundle when it builds. Declaring it as an ARG lets every build path
# supply it the same way — `docker build --build-arg`, `docker buildx bake`
# (see docker-bake.hcl) and Compose `build.args`. Promoting it to an ENV makes
# the same value available to the dev server (`npm run dev` reads it from the
# process env). It is a public backend URL, not a secret, so baking it in is
# intentional and safe — runtime secrets are never passed as build args.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

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
