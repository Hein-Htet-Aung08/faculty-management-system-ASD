FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY js/ /usr/share/nginx/html/js/

# Writes js/config.js from the API_BASE env var when the container starts
COPY 40-write-config.sh /docker-entrypoint.d/
RUN sed -i 's/\r$//' /docker-entrypoint.d/40-write-config.sh \
    && chmod +x /docker-entrypoint.d/40-write-config.sh

EXPOSE 80
