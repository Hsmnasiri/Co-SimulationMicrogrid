FROM python:3.11-slim
WORKDIR /app
COPY ieee33_sim.py ./
RUN pip install --no-cache-dir pandapower numpy influxdb
CMD ["python", "ieee33_sim.py"]
