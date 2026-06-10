FROM python:3.12-slim
WORKDIR usr/src/app

RUN apt-get update && \
        apt-get install -y ffmpeg && \
        apt-get install -y libpq-dev && \
        rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]
