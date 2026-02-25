# Stage 1: Compile ChatScript from source
FROM debian:bookworm-slim AS builder

RUN apt-get update \
 && apt-get install --no-install-recommends -y g++ make libcurl4-openssl-dev \
 && rm -rf /var/lib/apt/lists/*

COPY engine/SRC/ /build/SRC/
WORKDIR /build/SRC
RUN mkdir -p ../BINARIES && make clean server

# Stage 2: Runtime image
FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install --no-install-recommends -y libcurl4 \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/ChatScript/BINARIES /opt/ChatScript/LOGS \
    /opt/ChatScript/USERS /opt/ChatScript/TMP

COPY --from=builder /build/BINARIES/ChatScript /opt/ChatScript/BINARIES/ChatScript
COPY engine/DICT/ /opt/ChatScript/DICT/
COPY engine/LIVEDATA/ /opt/ChatScript/LIVEDATA/
COPY engine/TOPIC/ /opt/ChatScript/TOPIC/

VOLUME ["/opt/ChatScript/USERS/", "/opt/ChatScript/LOGS/"]

ENV LANG=C.UTF-8
EXPOSE 1024

WORKDIR /opt/ChatScript/BINARIES
ENTRYPOINT ["./ChatScript"]
