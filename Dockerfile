# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt 

COPY . /app
