FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r backend/requirements.txt

ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
