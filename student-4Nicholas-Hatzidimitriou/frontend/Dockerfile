FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY student-4Nicholas-Hatzidimitriou/frontend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY student-4Nicholas-Hatzidimitriou/frontend/ .
COPY shared/frontend/css /shared/frontend/css

COPY student-4Nicholas-Hatzidimitriou/frontend/nginx/default.conf.template /etc/nginx/templates/default.conf.template
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf
RUN chmod +x docker-entrypoint.sh

EXPOSE 8004

CMD ["./docker-entrypoint.sh"]
