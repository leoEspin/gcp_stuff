FROM python:3.9-slim

RUN mkdir -p  /app
COPY example.py /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install tensorflow google-cloud-storage

ENTRYPOINT ["python", "example.py"]
