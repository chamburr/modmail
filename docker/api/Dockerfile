FROM rust:1.60-alpine AS builder

RUN apk add --no-cache musl-dev openssl-dev

WORKDIR /build

COPY web/Cargo.toml web/Cargo.lock ./

RUN mkdir src
RUN echo 'fn main() {}' > src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/modmail*

COPY web/src ./src

RUN cargo build --release

FROM alpine:latest

RUN apk add --no-cache dumb-init

WORKDIR /app

COPY --from=builder /build/target/release/modmail ./

EXPOSE 6001

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["./modmail"]
