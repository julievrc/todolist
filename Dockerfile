FROM python:3.11.8-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy code into container
COPY . /app

# Create directory for Google credentials
RUN mkdir -p /app/credentials

# Copy the Google Cloud credentials file
# Note: The credential file should be mounted as a volume or secret in production
COPY trusty-shine-453002-b9-b9ba8ba27281.json /app/credentials/google-credentials.json

# Expose the port the app runs on
EXPOSE 5050

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
ENV GOOGLE_CLOUD_PROJECT=trusty-shine-453002-b9

# Run the app
CMD ["python", "todolist.py"]
