# --- Base: install deps once, reused by dev and build stages ---
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json ./
RUN npm install

# --- Dev stage: used by docker-compose.yml for local development with live reload ---
FROM base AS dev
COPY . .
EXPOSE 4200
CMD ["npm", "start"]

# --- Build stage: compiles the production bundle ---
FROM base AS build
ARG API_BASE_URL=/api/v1
COPY . .
# Bake the API base URL into the prod environment file before building
RUN sed -i "s#apiBaseUrl: \"/api/v1\"#apiBaseUrl: \"${API_BASE_URL}\"#" src/environments/environment.prod.ts
RUN npm run build

# --- Production stage: static files served by Nginx ---
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist/allocation-system-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O- http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
