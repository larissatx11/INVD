# Base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install dependencies
RUN pip install fastapi uvicorn

# Expose port
EXPOSE 8000

# Run the API
CMD ["uvicorn", "api_colmeia:app", "--host", "0.0.0.0", "--port", "8000"]
