FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py database.py init_db.py resource_config.py schema.py seed_data.py validation.py ./

RUN mkdir -p /app/data

EXPOSE 5105

CMD ["python", "app.py"]
