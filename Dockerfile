FROM python:3.8-alpine
WORKDIR /bot
COPY start.sh /bot/
RUN apk add --no-cache git zlib-dev python3-dev gcc musl-dev freetype-dev fribidi-dev harfbuzz-dev jpeg-dev lcms2-dev openjpeg-dev tcl-dev tiff-dev tk-dev

CMD ["/bin/sh", "start.sh"]
