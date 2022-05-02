FROM rust:1.60-slim-buster AS builder

RUN apt-get update && apt-get install -y musl-dev libpq-dev

RUN cargo install diesel_cli --no-default-features --features "postgres"

WORKDIR /build

RUN cp /usr/local/cargo/bin/diesel ./

FROM python:3.10-slim-buster

RUN apt update && apt install -y dumb-init
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install --no-cache-dir --no-index requirements.txt

RUN mkdir logs

COPY --from=builder /build ./bin

COPY docker/entrypoint.sh ./bin/
COPY main.py worker.py ./
COPY classes ./classes
COPY cogs ./cogs
COPY migrations ./migrations
COPY scripts ./scripts
COPY utils ./utils

EXPOSE 6002

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["./bin/entrypoint.sh"]
