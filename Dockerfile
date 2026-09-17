FROM python:3.12-slim

WORKDIR /app

# The image is standard-library only; keep bytecode out of the source tree.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime code only. Dataset/query inputs and output artifacts are mounted by the caller.
COPY run.py ./
COPY agents/ ./agents/
COPY rca/ ./rca/

# The official invocation supplies the python run.py command; this is only a convenient default.
CMD ["python", "run.py"]
