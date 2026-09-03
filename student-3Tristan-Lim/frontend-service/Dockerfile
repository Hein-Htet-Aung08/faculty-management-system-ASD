FROM nginx:alpine

COPY templates/ /usr/share/nginx/html/
COPY js/ /usr/share/nginx/html/js/

# The stylesheet is deliberately NOT copied here. The team maintains one unified
# CSS theme for the whole application, so /css is supplied at integration time -
# mounted from the shared directory by docker-compose:
#   volumes:
#     - ../shared/css:/usr/share/nginx/html/css:ro

COPY nginx.conf /etc/nginx/conf.d/default.conf

# nginx:alpine executes every script in this directory before starting.
COPY docker-entrypoint.sh /docker-entrypoint.d/40-backend-url.sh
RUN chmod +x /docker-entrypoint.d/40-backend-url.sh

EXPOSE 80
