FROM python:3.11-slim
 
WORKDIR /app
 
COPY requirements.txt .
 
RUN pip install --no-cache-dir -r requirements.txt
 
COPY app.py .
COPY init_db.py .
COPY seed.py .
 
RUN DATA_DIR=/app/data python init_db.py && DATA_DIR=/app/data python seed.py
 
EXPOSE 5104
 
CMD ["python", "app.py"]