FROM python:latest

WORKDIR /modmail

COPY requirements.txt .

RUN pip3 install -r requirements.txt && \
    chmod +x scripts/wait.sh

COPY . .

CMD ["sh", "-c", "'scripts/wait.sh rabbitmq:5672 -- python3 -u launcher.py'"]
