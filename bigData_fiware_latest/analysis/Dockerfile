FROM python:3.8-slim

COPY . /analysis

WORKDIR /analysis

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5050

CMD ["python", "analysis.py"]

