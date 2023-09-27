FROM rust:1.72-alpine AS builder

ENV RUSTFLAGS "-C target-feature=-crt-static"

RUN apk add --no-cache musl-dev openssl-dev

WORKDIR /build

COPY web/Cargo.toml web/Cargo.lock ./

RUN mkdir src
RUN echo 'fn main() {}' > src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/modmail*

COPY web/src ./src

RUN cargo build --release

FROM alpine:3.18

RUN apk add --no-cache dumb-init libgcc libssl1.1

WORKDIR /app

COPY --from=builder /build/target/release/modmail ./

EXPOSE 6001

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["./modmail"]
