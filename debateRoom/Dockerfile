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

#Debugging
RUN ls -R /app/users/static
# Collect static files (optional if needed)
RUN python manage.py collectstatic --noinput

# Apply database migrations (important for /admin to work)
RUN python manage.py migrate --noinput


# Expose port (Daphne default)
EXPOSE 8000
# Start with migration
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 debateRoom.asgi:application"]

