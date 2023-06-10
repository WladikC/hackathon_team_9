FROM python:3.10.0


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
CMD ["gunicorn", "app:app"]