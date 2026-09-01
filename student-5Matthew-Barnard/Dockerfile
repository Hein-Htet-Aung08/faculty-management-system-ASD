FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY database ./database
COPY frontend ./frontend

EXPOSE 5000

CMD ["python", "backend/app.py"]
