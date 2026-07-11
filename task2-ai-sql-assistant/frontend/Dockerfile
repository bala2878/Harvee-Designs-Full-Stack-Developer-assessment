FROM node:20-alpine AS base
WORKDIR /app
COPY package.json ./
RUN npm install

FROM base AS dev
COPY . .
EXPOSE 4201
CMD ["npm", "start"]

FROM base AS build
ARG API_BASE_URL=/api/v1
COPY . .
RUN sed -i "s#apiBaseUrl: \"/api/v1\"#apiBaseUrl: \"${API_BASE_URL}\"#" src/environments/environment.prod.ts
RUN npm run build

FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist/ai-sql-assistant-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O- http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
