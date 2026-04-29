FROM python:3.12-slim

WORKDIR /app

ENV UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install uv

RUN uv sync

RUN chmod +x entrypoint.sh

CMD ["sh", "entrypoint.sh"]