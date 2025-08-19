# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables to prevent Python from writing .pyc files
# and to keep it from buffering output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project directory into the container.
# This is mainly so the container has the code if the volume mount ever fails.
COPY . /app/

# Tell Docker that the container will listen on port 8000
EXPOSE 8000

# The command to run when the container starts.
# This runs the Django development server, which will auto-reload with a volume setup.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]