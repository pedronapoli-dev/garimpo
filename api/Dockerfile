FROM python:3.13-slim-bookworm

# uv installs exactly what uv.lock pins.
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv

WORKDIR /srv/api

# Dependencies first: this layer stays cached until the lockfile changes.
COPY pyproject.toml uv.lock .python-version ./
RUN UV_PYTHON_DOWNLOADS=never uv sync --locked --no-dev --no-install-project

COPY main.py ./
COPY app ./app
COPY migrations ./migrations
COPY docker-entrypoint.sh ./

# A non-root user that owns only the database directory.
RUN useradd --system --no-create-home garimpo \
    && mkdir /data \
    && chown garimpo /data
USER garimpo
VOLUME /data

ENV GARIMPO_ENV=production \
    GARIMPO_DATABASE_URL=sqlite:////data/garimpo.db \
    PATH=/srv/api/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
