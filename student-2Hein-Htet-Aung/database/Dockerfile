FROM python:3.11-slim

WORKDIR /app

COPY database/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY database/app.py ./app.py
COPY database/init_db.py ./init_db.py

RUN python init_db.py

EXPOSE 6002

CMD ["python", "app.py"]