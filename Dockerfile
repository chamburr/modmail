FROM python:latest

WORKDIR /modmail

COPY requirements.txt .

RUN pip3 install -r requirements.txt && \
    chmod +x scripts/wait.sh

COPY . .

CMD ["sh", "-c", "'python3 -u launcher.py'"]
