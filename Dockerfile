FROM python:3.13-slim AS builder
 
RUN mkdir /palette-messenger
WORKDIR /palette-messenger

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip
COPY requirements.txt /palette-messenger/
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim

RUN useradd -m -r palette-user && \
   mkdir /palette-messenger && \
   chown -R palette-user /palette-messenger

RUN mkdir -p /palette-messenger/logs /palette-messenger/static /palette-messenger/staticfiles /palette-messenger/media && \
   chmod -R 0777 /palette-messenger/logs /palette-messenger/static /palette-messenger/staticfiles /palette-messenger/media || true && \
   chown -R palette-user:palette-user /palette-messenger/logs /palette-messenger/static /palette-messenger/staticfiles /palette-messenger/media

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /palette-messenger

COPY --chown=palette-user:palette-user . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
EXPOSE 8001

RUN chmod +x /palette-messenger/entrypoint.prod.sh /palette-messenger/entrypoint.prod.sh

CMD ["/palette-messenger/entrypoint.prod.sh"]