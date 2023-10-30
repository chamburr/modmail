#!/bin/bash

WORKDIR=$(pwd)

echo "Linting Rust..."
cd "$WORKDIR/web" && cargo clippy

echo "Linting Node..."
cd "$WORKDIR/web" && yarn --silent lint

echo "Linting Python..."
cd "$WORKDIR/cogs" && flake8
cd "$WORKDIR/classes" && flake8
