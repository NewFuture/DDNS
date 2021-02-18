FROM six8/pyinstaller-alpine:alpine-3.6-pyinstaller-v3.4
WORKDIR /app
COPY . .
RUN pyinstaller --onefile --noconfirm --clean ./.build/ddns.spec

FROM alpine:latest
LABEL maintainer="NN708"
COPY --from=0 /app/dist/ddns /
RUN echo "*/5 * * * *   /ddns -c /config.json" > /etc/crontabs/root
CMD [ "crond", "-f" ]
