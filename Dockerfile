FROM python:3.12-slim

WORKDIR /app

# The image is standard-library only; keep bytecode out of the source tree.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime code only. Dataset/query inputs and output artifacts are mounted by the caller.
COPY run.py ./
COPY agents/ ./agents/
COPY rca/ ./rca/
COPY libraries/trace_semantics/src/trace_semantics/ ./libraries/trace_semantics/src/trace_semantics/
COPY libraries/rca_domain/src/rca_domain/ ./libraries/rca_domain/src/rca_domain/
COPY scripts/demo_discovery.py scripts/demo_investigation.py scripts/validate_discovery.py ./scripts/

# The official invocation supplies the python run.py command; this is only a convenient default.
CMD ["python", "run.py"]
