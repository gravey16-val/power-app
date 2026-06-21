# Single-stage image (project rule: no multi-stage builds).
FROM node:20-alpine

WORKDIR /app

# No package-lock.json is committed for the M1 scaffold, so we use `npm install`
# rather than `npm ci`. See DECISIONS.md.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Vite dev server, bound to 0.0.0.0 so it is reachable from the host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
