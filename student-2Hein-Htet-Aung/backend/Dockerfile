FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY prompts/allocation ./prompts/allocation

EXPOSE 5002

CMD ["python", "backend/app.py"]