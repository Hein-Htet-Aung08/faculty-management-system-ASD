FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema.py .
COPY init_db.py .
COPY app.py .

RUN python init_db.py

EXPOSE 5302

CMD ["python", "app.py"]
