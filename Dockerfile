FROM alpine:latest as download
ARG SEAFILE_VERSION
ENV SEAFILE_VERSION=${SEAFILE_VERSION}

# Get Seafile install archive
RUN mkdir -p /seafile/data && mkdir -p /seafile/server
ADD https://download.seadrive.org/seafile-server_${SEAFILE_VERSION}_x86-64.tar.gz .
RUN tar -zxvf seafile-server_${SEAFILE_VERSION}_x86-64.tar.gz && \
    mv seafile-server-${SEAFILE_VERSION} /seafile/server/seafile-server

# Copy scripts
COPY container_scripts/setup_script.py /seafile
COPY container_scripts/docker_entrypoint.sh /seafile


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
COPY --from=download --chown=33:33 /seafile /seafile
COPY container_scripts/backup /usr/sbin

RUN set -eux; \
    # Installing Seahub dependencies
    pip3 install --no-cache-dir --no-dependencies \
        captcha==0.4 \
        django-simple-captcha==0.5.17 \
        django-ranged-response==0.2.0 \
        pycryptodome==3.16.0 \
        Pillow==9.3.0 \
    ; \
    # Installing Seafdav dependencies
    pip3 install --no-cache-dir --no-dependencies \
        markupsafe==2.0.1 \
        Jinja2~=2.10 \
        sqlalchemy==1.4.44 \
        lxml==4.9.1

ENV PYTHONPATH=/seafile/server/seafile-server/seahub/thirdpart:/seafile/server/seafile-server/seafile/lib/python3/site-packages

ARG SEAFILE_VERSION
ENV SEAFILE_VERSION=${SEAFILE_VERSION}

USER 33
WORKDIR /seafile
EXPOSE 8000 8082 8080
VOLUME /seafile/data
ENTRYPOINT ["/tini", "-g", "--"]
CMD ["bash", "-c", "/seafile/docker_entrypoint.sh"]
