# Frontend — Weather Dashboard (React + Vite dev server).
# Single-stage build (NO multi-stage), per project Docker rules.
FROM node:20-alpine

WORKDIR /app

# Install dependencies first so the layer caches when only source changes.
# No committed package-lock.json yet (M1 scaffold), so use `npm install`.
COPY package.json ./
RUN npm install

# Copy the rest of the application source.
COPY . .

EXPOSE 5173

# Vite dev server, bound to 0.0.0.0 so it's reachable from the host.
# VITE_API_URL is read from the environment (see docker-compose.yml) at build/dev time.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
