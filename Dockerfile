FROM python:3.11-slim

RUN mkdir /app
WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

ADD requirements.txt /app/requirements.txt

RUN pip3.11 install -r requirements.txt --no-cache-dir

COPY . /app

EXPOSE 80
CMD python3.11 /app/main.py --config config-production.yaml
