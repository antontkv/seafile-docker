FROM alpine:latest as download
ARG SEAFILE_VERSION
ENV SEAFILE_VERSION=${SEAFILE_VERSION}
ADD https://download.seadrive.org/seafile-server_${SEAFILE_VERSION}_x86-64.tar.gz .
RUN tar -zxvf seafile-server_${SEAFILE_VERSION}_x86-64.tar.gz && \
    mv seafile-server-${SEAFILE_VERSION} seafile-server

FROM ubuntu:focal as runtime
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN set -eux; \
    apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y --no-install-recommends \
        tzdata \
        python3 python3-setuptools python3-pip \
        pwgen \
        sqlite3 \
    ; \
    rm -rf /var/lib/apt/lists/*

# Install tini for init
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini

# Get Seafile files
RUN mkdir -p /seafile/data && mkdir -p /seafile/server
COPY --from=download /seafile-server /seafile/server/seafile-server

RUN set -eux; \
    # Installing Seahub dependencies
    pip3 install --no-cache-dir --no-dependencies \
        captcha==0.3 \
        django-simple-captcha==0.5.12 \
        django-ranged-response==0.2.0 \
        pycryptodome==3.9.7 \
        Pillow==7.0.0 \
    ; \
    # Installing Seafdav dependencies
    pip3 install --no-cache-dir --no-dependencies \
        markupsafe==2.0.1 \
        Jinja2~=2.10 \
        sqlalchemy==1.3.7

COPY container_scripts/setup_script.py /seafile
COPY container_scripts/docker_entrypoint.sh /seafile
COPY container_scripts/backup /usr/sbin

ENV PYTHONPATH=/seafile/server/seafile-server/seahub/thirdpart:/seafile/server/seafile-server/seafile/lib64/python3.6/site-packages

ARG SEAFILE_VERSION
ENV SEAFILE_VERSION=${SEAFILE_VERSION}

RUN chown -R 33:33 /seafile
USER 33
WORKDIR /seafile
EXPOSE 8000 8082 8080
VOLUME /seafile/data
ENTRYPOINT ["/tini", "-g", "--"]
CMD ["bash", "-c", "/seafile/docker_entrypoint.sh"]
