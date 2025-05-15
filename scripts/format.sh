#!/bin/bash

WORKDIR=$(pwd)

echo "Formatting Rust..."
cd "$WORKDIR/web" && cargo fmt

echo "Formatting Node..."
cd "$WORKDIR/web" && yarn --silent format --log-level warn

echo "Formatting Python..."
cd "$WORKDIR" && isort . && black . --line-length 100
