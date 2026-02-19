# ---- Build Stage ----
FROM node:20-slim AS build

WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json ./
RUN npm install

# Copy source and build
COPY . .
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# ---- Production Stage ----
FROM node:20-slim

WORKDIR /app

# Copy the built output from the build stage
COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules

EXPOSE 8080
ENV PORT=8080

CMD ["node", "build"]
