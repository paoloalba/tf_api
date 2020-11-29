FROM python:3.6-slim
# FROM ubuntu:18.04

ADD /application /app

WORKDIR /app/

RUN mkdir -p sharedstorage

RUN chmod +x ./progr_create_cert.sh

ENTRYPOINT ["./progr_create_cert.sh"]
