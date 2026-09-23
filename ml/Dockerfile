FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/qor

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ml /opt/qor/ml
COPY scripts /opt/qor/scripts
COPY backend /opt/qor/backend

WORKDIR /opt/qor/backend
ENV PYTHONUNBUFFERED=1
ENV IEK_DATA_DIR=/data/iek

EXPOSE 8002

CMD ["uvicorn", "qor.ml_server:app", "--host", "0.0.0.0", "--port", "8002"]
