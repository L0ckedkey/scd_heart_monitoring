# Base image
FROM gregoriusnatanael99/scd_flask:cloud_1

# Set environment variables
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/service-account-key.json"

# Set working directory
WORKDIR /app

# Copy your application code (adjust as needed)
COPY . /app

# Copy the Google Cloud credentials JSON file into the image
COPY service-account-key.json /app/service-account-key.json

# Expose the application port (adjust if needed)
EXPOSE 8003

# Start the Flask app
CMD ["python3", "app.py"]

