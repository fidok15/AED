# Build context: frontend/ (docker compose sets it, plus the named contexts "docker" and "standard").
# Builds the dane.gov.pl frontend fork with the AED module and serves it with nginx,
# which also proxies /api/aed to the AED service and the rest of /api to the public portal API.
# Official images pulled through the AWS public mirror: Docker Hub rate-limits anonymous pulls (HTTP 429).
ARG NODE_IMAGE=public.ecr.aws/docker/library/node:20-alpine
ARG NGINX_IMAGE=public.ecr.aws/docker/library/nginx:1.27-alpine
FROM ${NODE_IMAGE} AS build
WORKDIR /work/frontend
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
# The AED module imports the data standard from ../aed_standard/schema.json (single source of truth).
COPY --from=standard schema.json /work/aed_standard/schema.json
RUN npm run build:aed

FROM ${NGINX_IMAGE}
COPY --from=build /work/frontend/dist/frontend/browser /usr/share/nginx/html
# The official image renders *.template with environment variables at start.
COPY --from=docker nginx.conf.template /etc/nginx/templates/default.conf.template
ENV AED_SERVICE_URL=http://aed-service:8085
EXPOSE 80
