FROM python:3.9-slim

WORKDIR /app

# Copy dependency files
COPY requirements.txt /app/requirements.txt

# Install packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . /app

# Cloud Run defaults to port 8080
EXPOSE 8080

# Execute server using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
