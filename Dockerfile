FROM alpine:latest as download
ARG SEAFILE_VERSION
ENV SEAFILE_VERSION=${SEAFILE_VERSION}
ADD https://download.seadrive.org/seafile-server_${SEAFILE_VERSION}_x86-64.tar.gz .
RUN tar -zxvf seafile-server_${SEAFILE_VERSION}_x86-64.tar.gz && \
    mv seafile-server-${SEAFILE_VERSION} seafile-server

FROM python:3.11.2-slim-bullseye as runtime
ARG SEAFILE_VERSION
ENV SEAFILE_VERSION=${SEAFILE_VERSION}
RUN set -eux; \
    apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y --no-install-recommends \
        pwgen \
        sqlite3 \
        tini \
    ; \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /seafile/data && mkdir -p /seafile/server
COPY --from=download /seafile-server /seafile/server/seafile-server
RUN ls -la /seafile/server/seafile-server
RUN chown -R 33:33 /seafile

RUN pip install --no-cache-dir -r /seafile/server/seafile-server/seahub/requirements.txt

USER 33
WORKDIR /seafile
EXPOSE 8000 8082 8080
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
