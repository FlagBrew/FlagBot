FROM python:3
RUN apt update && \
    apt install mono-complete zlib1g-dev gcc musl-dev gcc libfreetype-dev libfribidi-dev libharfbuzz-dev libjpeg-dev liblcms2-2 libopenjp2-7-dev libtiff-dev -y

WORKDIR /bot
COPY start.sh /bot/
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["/bin/sh", "start.sh"]

