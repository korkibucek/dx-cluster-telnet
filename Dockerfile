FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
RUN pip install --no-cache-dir .
RUN useradd --system --create-home --home-dir /var/lib/rbn-dxcluster rbn && mkdir -p /app/data && chown -R rbn:rbn /app/data
USER rbn
EXPOSE 7373 8080
CMD ["rbn-dxcluster", "serve", "--config", "config/config.example.yaml"]
