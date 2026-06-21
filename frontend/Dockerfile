FROM node:20-alpine

WORKDIR /app

# No package-lock.json is committed yet (see DECISIONS.md), so use `npm install`.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
