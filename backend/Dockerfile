FROM python:3.12-alpine
ENV OJ_ENV=production
WORKDIR /app

# 1. Install System Dependencies
# Added 'shadow' (for useradd) and 'supervisor' (for prod compatibility)
RUN apk add --no-cache gcc libc-dev python3-dev libpq libpq-dev \
    libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev freetype freetype-dev \
    curl unzip shadow supervisor

# 2. Create the Users explicitly here (so we don't depend on entrypoint.sh)
RUN groupadd -r spj && useradd -r -g spj spj && \
    useradd -r server

# 3. Install Python Dependencies
# Note: build context is ./backend, so paths are relative to that.
COPY ./deploy/requirements.txt /app/deploy/
RUN pip install --no-cache-dir -r /app/deploy/requirements.txt

# 4. Copy Source Code
COPY ./ /app/
RUN chmod +x ./deploy/entrypoint.sh

EXPOSE 8000
ENTRYPOINT [ "/app/deploy/entrypoint.sh" ]