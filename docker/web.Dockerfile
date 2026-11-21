# Build context: frontend/ (docker compose sets it, plus the named contexts "docker" and "standard").
# Builds the dane.gov.pl frontend fork with the AED module and serves it with nginx,
# which also proxies /api/aed to the AED service and the rest of /api to the public portal API.
FROM node:20-alpine AS build
WORKDIR /work/frontend
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
# The AED module imports the data standard from ../aed_standard/schema.json (single source of truth).
COPY --from=standard schema.json /work/aed_standard/schema.json
RUN npm run build:aed

FROM nginx:1.27-alpine
COPY --from=build /work/frontend/dist/frontend/browser /usr/share/nginx/html
# The official image renders *.template with environment variables at start.
COPY --from=docker nginx.conf.template /etc/nginx/templates/default.conf.template
ENV AED_SERVICE_URL=http://aed-service:8085
EXPOSE 80
