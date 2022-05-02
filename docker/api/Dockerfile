FROM rust:1.60-alpine AS builder

WORKDIR /build

COPY web/Cargo.toml web/Cargo.lock ./
COPY web/.cargo ./.cargo

RUN touch -p src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/modmail*

COPY web/src ./src

RUN cargo build --release

FROM alpine:latest

RUN apk add dumb-init --no-cache

WORKDIR /app

COPY --from=builder /build/target/release/modmail ./

EXPOSE 6001

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["./modmail"]
