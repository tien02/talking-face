ARG BASE_IMAGE=pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && \
    apt-get install -y \
    git \
    ffmpeg \
    build-essential \
    cmake \
    curl \
    wget \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /module

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

WORKDIR /module/src
COPY ./app /module/app
COPY ./common /module/common
COPY ./config /module/config
COPY ./schemas /module/schemas
COPY ./src /module/src
COPY ./pyproject.toml /module/pyproject.toml
COPY ./ray_serve_config.yaml /module/ray_serve_config.yaml

WORKDIR /module
RUN pip install -e .