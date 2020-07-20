FROM six8/pyinstaller-alpine:latest
WORKDIR /app
COPY . .
RUN pyinstaller --onefile --noconfirm --clean ./.build/ddns.spec

FROM alpine:latest
COPY --from=0 /app/dist/ddns /
CMD [ "/ddns" ]