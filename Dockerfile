FROM python:alpine

WORKDIR /modmail

COPY requirements.txt ./

RUN apk --no-cache add curl build-base linux-headers && \
	curl -sSf https://sh.rustup.rs | sh -s -- --profile minimal --default-toolchain nightly -y && \
	source $HOME/.cargo/env && \
	pip3 install -r requirements.txt

COPY . .
