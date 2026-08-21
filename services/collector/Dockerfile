FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
WORKDIR /app
COPY services/collector /app/services/collector
RUN pip install --no-cache-dir /app/services/collector
COPY config /app/config
COPY contracts /app/contracts
ENTRYPOINT ["python", "-m", "report_collector"]
