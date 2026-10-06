# Evaluation harness: Python standard library only, no third-party packages.
FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "swisscivicqa.pipeline"]
CMD ["verify"]
