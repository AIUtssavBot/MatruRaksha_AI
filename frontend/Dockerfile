<<<<<<< HEAD
# Frontend Dockerfile (Development)
FROM node:20-alpine

# Install dependencies required
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (use ci for deterministic installs)
RUN npm ci

# Copy application code
COPY . .

RUN npm run build

# Expose Vite's default port
EXPOSE 5173

# Start Vite dev server with host set to allow external connections
CMD ["npm", "run", "start"]
=======
### Multi-stage Dockerfile for frontend (Vite + React)
### Stage 1: build
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
# Use `npm install` (no package-lock.json in repo). Keep output quiet and skip audit for faster builds.
RUN npm install --silent --no-audit --no-fund

# Copy source
COPY frontend/ ./

# Accept build-time VITE_* variables (optional)
ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# If build args provided, write a .env.production file Vite will pick up
RUN if [ -n "$VITE_API_URL" ] || [ -n "$VITE_SUPABASE_URL" ] || [ -n "$VITE_SUPABASE_ANON_KEY" ]; then \
      printf '%s\n' "VITE_API_URL=${VITE_API_URL}" "VITE_SUPABASE_URL=${VITE_SUPABASE_URL}" "VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}" > .env.production; \
    fi

# Build the production bundle
RUN npm run build

### Stage 2: serve with nginx
FROM nginx:stable-alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Add SPA-friendly nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
>>>>>>> 6eb2a328ef725bea436f28cc077fc497fe3c112b
