FROM python:3.12-slim

WORKDIR /opt/honey-agent

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dashboard ./dashboard
COPY .env.example ./.env.example

ENV PYTHONPATH=/opt/honey-agent/src
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "honey_agent.composition.main"]
