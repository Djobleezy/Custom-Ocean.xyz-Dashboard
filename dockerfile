FROM python:3.9-slim

WORKDIR /app

# Install curl for healthcheck and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY *.py .
COPY config.json .
COPY setup.py .

# Create necessary directories
RUN mkdir -p static/css static/js templates logs

# Copy static files and templates
COPY static/css/*.css static/css/
COPY static/js/*.js static/js/
COPY templates/*.html templates/

# Run the setup script to ensure proper organization
RUN python setup.py

# Create a non-root user for better security
RUN adduser --disabled-password --gecos '' appuser

# Change ownership of the /app directory so appuser can write files
RUN chown -R appuser:appuser /app

# Create a directory for logs with proper permissions
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHON_UNBUFFERED=1

# Add healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Use Gunicorn as the production WSGI server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "App:app", \
     "--workers=1", \
     "--threads=12", \
     "--timeout=600", \
     "--keep-alive=5", \
     "--log-level=info", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "--log-file=-", \
     "--graceful-timeout=60", \
     "--worker-tmp-dir=/dev/shm"]