FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY business_tools ./business_tools
COPY asgi_app.py .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "asgi_app:app", "--host", "0.0.0.0", "--port", "8000"]
