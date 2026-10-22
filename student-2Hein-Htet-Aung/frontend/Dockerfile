FROM nginx:alpine

COPY student-2Hein-Htet-Aung/frontend/index.html /usr/share/nginx/html/index.html
COPY student-2Hein-Htet-Aung/frontend/js/ /usr/share/nginx/html/js/
COPY ./shared/frontend/css/styles.css /usr/share/nginx/html/css/styles.css
COPY student-2Hein-Htet-Aung/frontend/40-write-config.sh /docker-entrypoint.d/40-write-config.sh
RUN sed -i 's/\r$//' /docker-entrypoint.d/40-write-config.sh \
    && chmod +x /docker-entrypoint.d/40-write-config.sh

EXPOSE 80