# We use Python Alpine for small size (ARM64 compatible)
FROM python:3.12-alpine
ENV OJ_ENV production
WORKDIR /app

# Install System Dependencies (Postgres, JPEG, Compiler)
RUN apk add --no-cache gcc libc-dev python3-dev libpq libpq-dev \
    libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev freetype freetype-dev \
    curl unzip

# Install Python Dependencies
COPY ./deploy/requirements.txt /app/deploy/
RUN pip install --no-cache-dir -r /app/deploy/requirements.txt

# Copy Source Code
COPY ./ /app/
RUN chmod +x ./deploy/entrypoint.sh

# We expose 8000.
# In Prod: Gunicorn runs via entrypoint.sh
# In Dev: We override CMD to run 'manage.py runserver'
EXPOSE 8000
ENTRYPOINT [ "/app/deploy/entrypoint.sh" ]