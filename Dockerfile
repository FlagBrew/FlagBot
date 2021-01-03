FROM python:3.8-alpine
WORKDIR /bot
COPY . /bot/

CMD ["start.sh"]
