FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Al usar SQLite y psycopg2-binary, no necesitamos gcc ni libpq-dev
# Esto evita errores de DNS durante el build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear estructura para archivos estáticos
RUN mkdir -p static/capturas && chmod -R 777 static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]