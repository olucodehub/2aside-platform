# 2-Aside Funding Service - Updated for Azure Container Apps
FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install SQL Server ODBC Driver
RUN apt-get update && apt-get install -y \
    curl apt-transport-https gnupg2 unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy shared module first
COPY ../shared ./shared/

# Copy service requirements and install
COPY funding-service/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy service code
COPY funding-service/ ./

# Create uploads directory for local fallback
RUN mkdir -p uploads/payment_proofs

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
