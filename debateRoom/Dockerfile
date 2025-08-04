# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /requirements.txt 
RUN pip install --no-cache-dir -r /requirements.txt

# Copy project files
COPY . .


# Collect static files (optional if needed)
RUN python manage.py collectstatic --noinput


# Expose port (Daphne default)
EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "debateRoom.asgi:application"]