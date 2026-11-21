# Build context: repository root (docker compose sets it).
# Official image pulled through the AWS public mirror: Docker Hub rate-limits anonymous pulls (HTTP 429).
ARG PYTHON_IMAGE=public.ecr.aws/docker/library/python:3.13-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app
COPY aed_service/requirements.txt aed_service/requirements.txt
RUN pip install --no-cache-dir -r aed_service/requirements.txt

COPY aed_standard aed_standard
COPY aed_service aed_service
# Raw sources: the first start imports the national registry from them.
COPY scripts scripts
COPY datasets/raw datasets/raw

# Run as a non-root user; the database lives on a volume.
# The scheduled refresh rewrites the raw snapshot, so the service user must own it too.
RUN useradd --system --create-home aed && mkdir /data && chown aed /data && chown -R aed /app/datasets
USER aed

ENV AED_PORT=8085 AED_DB=/data/aed_service.db PYTHONUNBUFFERED=1
EXPOSE 8085
CMD ["python", "-m", "aed_service"]
