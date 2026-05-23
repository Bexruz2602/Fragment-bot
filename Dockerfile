FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
