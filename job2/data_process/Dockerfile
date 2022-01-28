FROM python:3.8-slim-buster
COPY requirements.txt requirements.txt

ARG INFLUX_DB_NAME
ARG INFLUX_DB_HOST
ARG DS_NAME
ARG DS_HOST

ENV INFLUX_DB_NAME=${INFLUX_DB_NAME}
ENV INFLUX_DB_HOST=${INFLUX_DB_HOST}
ENV DS_NAME=${DS_NAME}
ENV DS_HOST=${DS_HOST}

RUN pip3 install -r requirements.txt
SHELL ["/bin/bash", "-c"]
COPY . .
CMD python3 data_process.py $INFLUX_DB_NAME $INFLUX_DB_HOST $DS_NAME $DS_HOST
