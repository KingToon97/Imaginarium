FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy package source
COPY . .
RUN pip install --no-cache-dir -e .

# Runtime data goes in a named volume
ENV IMAGINARIUM_HOME=/data
VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "imaginarium.server:server", "--host", "0.0.0.0", "--port", "8000"]
