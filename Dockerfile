# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install required Python packages, pin openai to an older version
RUN pip install --no-cache-dir ebooklib beautifulsoup4 lxml openai==0.28

# Command to run the script
CMD ["python", "summarize.py"]
