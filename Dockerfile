# Docker file is a text document that contains all the commands a user could call on the command line to assemble an image 
# => DOCKER can build images automatically by reading the instructions from a Dockerfile.


# Base image for python
FROM python:3.11-slim

# environment variables to prevent python from writing pyc files to disc and to ensure that python output is sent straight to terminal without being buffered
# and for debian frontend is for non-interactive mode to avoid prompts during package installation
ENV PYTHONDONTWRITEBYTECODE=1\
    PYTHONUNBUFFERED=1\
    DEBIAN_FRONTEND=noninteractive

# Install dependencies juste for latex and fonts because we need to compile the latex files into pdfs nothing else
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    lmodern \
    fonts-font-awesome \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# Create a non-root user and group to run the application for security reasons
# and if i want to system user i will use the command useradd -r -u 1001 -g appgroup -m -s /bin/bash appuser
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser


# Set the working directory inside the container to /app its always a good practice to set a working directory for your application inside the container, so that all subsequent commands are run in that directory.
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt .
# Install the dependencies from requirements.txt using pip, with no cache to reduce image size and upgrade pip to the latest version
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app and change ownership of the /app directory to the non-root user and group created earlier
COPY . .
RUN chown -R appuser:appgroup /app

# Switch to the non-root user to run the application for security reasons
USER appuser

# Expose port 8501 for the application to be accessible from outside the container
EXPOSE 8501



# Healthcheck to ensure that the application is running and healthy, by sending a request to the health endpoint of the application and checking for a successful response. If the health check fails, the container will be marked as unhealthy.
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
# CMD instruction specifies the command to run when the container starts. In this case, it runs the Streamlit application defined in app.py, listening on port 8501 and accessible from any network interface ( for example, if you want to access the application from your host machine or from other containers in the same network). 
# The CMD instruction can be overridden at runtime by specifying a different command when starting the container.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]