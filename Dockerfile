# syntax=docker/dockerfile:1

FROM python:3.6

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3.6 install -r requirements.txt

COPY src/ .
COPY main.py .
COPY .env .

CMD ["python3.6", "main.py"]
