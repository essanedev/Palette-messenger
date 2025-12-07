# Stage 1: Base build stage
FROM python:3.13-slim AS builder
 
# Create the app directory
RUN mkdir /palette-messenger
 
# Set the working directory
WORKDIR /palette-messenger
 
# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
# Install dependencies first for caching benefit
RUN pip install --upgrade pip 
COPY requirements.txt /palette-messenger/ 
RUN pip install --no-cache-dir -r requirements.txt
 
# Stage 2: Production stage
FROM python:3.13-slim
 
RUN useradd -m -r palette-user && \
   mkdir /palette-messenger && \
   chown -R palette-user /palette-messenger

# Ensure logs directory exists and static folders are writable by the application user
RUN mkdir -p /palette-messenger/logs && \
   chown -R palette-user:palette-user /palette-messenger/logs && \
   chown -R palette-user:palette-user /palette-messenger/staticfiles && \
   chown -R palette-user:palette-user /palette-messenger/static
 
# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
 
# Set the working directory
WORKDIR /palette-messenger
 
# Copy application code
COPY --chown=palette-user:palette-user . .
 
# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
# Switch to non-root user
USER palette-user
 
# Expose the application port
EXPOSE 8000 

# Make entry file executable
RUN chmod +x  /palette-messenger/entrypoint.dev.sh
 
# Start the application using Gunicorn
CMD ["/palette-messenger/entrypoint.dev.sh"]