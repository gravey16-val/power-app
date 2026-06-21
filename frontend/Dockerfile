FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better layer caching. `npm ci` uses the
# committed lockfile for reproducible installs.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
