FROM alpine:latest
WORKDIR /app
COPY . .
RUN apk add --no-cache python3 py3-pip python3-dev patchelf build-base
RUN pip3 install -U nuitka --break-system-packages
RUN .build/nuitka.cmd

FROM alpine:latest
LABEL maintainer="NN708, newfuture"
COPY --from=0 /app/.build/entrypoint.sh /
COPY --from=0 /app/dist/ddns /
ENTRYPOINT [ "/entrypoint.sh" ]
