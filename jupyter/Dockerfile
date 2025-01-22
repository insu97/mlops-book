FROM jupyter/datascience-notebook:python-3.10.9

USER root
RUN userdel -r jovyan \
    && useradd -m -s /bin/bash -N -u 1000 insu \
    && chown -R insu:users /home/insu

USER insu
WORKDIR /home/insu

