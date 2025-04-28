FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r backend/requirements.txt

ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

RUN pip install --upgrade pip
RUN pip install -r backend/requirements.txt

CMD ["python", "-m", "backend.app"]
