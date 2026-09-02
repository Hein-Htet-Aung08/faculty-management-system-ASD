FROM python:3.11-slim

WORKDIR /app

COPY backend-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend-service ./backend-service
COPY prompts ./prompts

EXPOSE 5003

CMD ["python", "backend-service/app.py"]
