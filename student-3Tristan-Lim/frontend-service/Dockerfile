FROM nginx:alpine

COPY templates/ /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

# nginx:alpine executes every script in this directory before starting.
COPY docker-entrypoint.sh /docker-entrypoint.d/40-backend-url.sh
RUN chmod +x /docker-entrypoint.d/40-backend-url.sh

EXPOSE 80
