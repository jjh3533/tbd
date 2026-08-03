FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir nicegui requests beautifulsoup4 yfinance python-dotenv apscheduler pytz bcrypt anthropic openpyxl playwright
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8080

CMD ["python3", "dashboard/app.py"]
