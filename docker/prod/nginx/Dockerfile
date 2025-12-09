FROM nginx:latest

RUN rm -f /etc/nginx/conf.d/default.conf

COPY ./docker/prod/nginx/django_nginx.conf /etc/nginx/conf.d/
