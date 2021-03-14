FROM python:latest

WORKDIR /modmail

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-u", "launcher.py"]
