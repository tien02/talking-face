ARG BASE_IMAGE=pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y \
    git curl build-essential cmake yasm nasm pkg-config autoconf automake \
    libtool libv4l-dev libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libmp3lame-dev librtmp-dev libfdk-aac-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/src

# Build and install x264 (shared)
RUN git clone --branch stable https://code.videolan.org/videolan/x264.git && \
    cd x264 && \
    ./configure --prefix=/usr/local --enable-pic --enable-shared && \
    make -j"$(nproc)" && \
    make install && \
    cd .. && rm -rf x264

# Build and install FFmpeg with libx264, mp3lame, librtmp, aac
RUN git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg && \
    cd ffmpeg && \
    ./configure \
        --prefix=/usr/local \
        --enable-gpl \
        --enable-nonfree \
        --enable-libx264 \
        --enable-libmp3lame \
        --enable-librtmp \
        --enable-libfdk-aac \
        --enable-shared && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig && \
    cd .. && rm -rf ffmpeg

RUN rm -f /opt/conda/bin/ffmpeg /opt/conda/bin/ffprobe

RUN ln -s /usr/local/bin/ffmpeg /opt/conda/bin/ffmpeg && \
    ln -s /usr/local/bin/ffprobe /opt/conda/bin/ffprobe

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