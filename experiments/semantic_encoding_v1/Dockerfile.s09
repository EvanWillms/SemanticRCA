FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements-live.txt /app/requirements-live.txt
RUN python -m pip install --no-cache-dir -r /app/requirements-live.txt

COPY __init__.py run_s02_s09.py run_s09_live.py test_s09_transport.py /app/experiments/semantic_encoding_v1/
COPY fixtures/expected_s09.json /app/experiments/semantic_encoding_v1/fixtures/expected_s09.json

CMD ["python", "-m", "experiments.semantic_encoding_v1.run_s09_live", "--help"]
