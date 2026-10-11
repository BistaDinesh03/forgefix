# syntax=docker/dockerfile:1
# Build stage: create a self-contained virtualenv.
FROM python:3.12-slim AS build
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY forgefix ./forgefix
RUN pip install --no-cache-dir .

# Runtime stage: non-root, minimal image, venv copied from build.
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin forgefix
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER forgefix
WORKDIR /work
ENTRYPOINT ["forgefix"]
CMD ["--help"]
