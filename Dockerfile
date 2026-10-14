# 1. Use an official lightweight Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker caching layers
COPY requirements.txt .

# 4. Install the required system dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code into the container
COPY . .

# 6. Expose the port that FastAPI runs on
EXPOSE 8000

# 7. Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
