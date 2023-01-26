FROM python:3.8-slim

COPY . /sensor

WORKDIR /sensor

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

CMD ["python", "sensor.py"]

