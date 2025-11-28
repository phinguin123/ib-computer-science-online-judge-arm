# --- Stage 1: Build the C Sandbox (Judger) & Python Bindings ---
# ARM64: debian:bookworm-slim has native ARM64 support
FROM debian:bookworm-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install build tools
# ARM64: All build tools compile natively for ARM64 architecture
RUN apt-get update && apt-get install -y \
    libtool make cmake libseccomp-dev gcc g++ python3 python3-venv python3-pip git \
    && rm -rf /var/lib/apt/lists/*

# Install 'build' tool for pyproject.toml support
RUN pip3 install --break-system-packages build

# Copy the Judger source code
COPY Judger/ /app/Judger

# 1. Compile libjudger.so (The C Sandbox)
# ARM64: CMake will automatically detect ARM64 and compile accordingly
# The -fPIC flag in CMakeLists.txt ensures position-independent code for ARM
WORKDIR /app/Judger
RUN mkdir build && cd build && cmake .. && make && make install

# 2. Build Python bindings (using modern build tool)
WORKDIR /app/Judger/bindings/Python
RUN python3 -m build


# --- Stage 2: The Final Runtime Image ---
# ARM64: debian:bookworm-slim has native ARM64 support
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install Runtime Dependencies
# ARM64: All runtime dependencies are available for ARM64
# We need 'gcc' here to compile unbuffer.c later (compiles natively for ARM)
RUN apt-get update && apt-get install -y \
    python3-minimal python3-venv libpython3-stdlib libpython3-dev \
    golang-go \
    openjdk-17-jdk \
    gcc g++ \
    nodejs npm \
    strace \
    libseccomp-dev \
    curl gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create the specific users required by the Sandbox
RUN useradd -u 901 -r -s /sbin/nologin -M compiler && \
    useradd -u 902 -r -s /sbin/nologin -M code && \
    useradd -u 903 -r -s /sbin/nologin -M -G code spj

# Copy the compiled artifacts from Stage 1
# FIX: CMakeLists.txt installs to /usr/lib/judger/libjudger.so, not /usr/local/lib
RUN mkdir -p /usr/lib/judger
COPY --from=builder /usr/lib/judger/libjudger.so /usr/lib/judger/libjudger.so
COPY --from=builder /app/Judger/bindings/Python/dist/ /app/dist/

# --- FIX: Install Python Dependencies Manually ---
# We manually list the packages because requirements.txt does not exist
RUN python3 -m venv .venv && \
    .venv/bin/pip install --no-cache-dir flask gunicorn idna psutil requests && \
    .venv/bin/pip install /app/dist/*.whl

# Copy the Server Code
# The official repo puts the python code in a 'server' folder
COPY server/ /app/

# Compile the output buffer tool
# This file is inside the server/ folder we just copied
# ARM64: -fPIC ensures position-independent code for ARM architecture
RUN gcc -shared -fPIC -o unbuffer.so unbuffer.c

# Set permissions
RUN chmod -R 755 /app && chmod +x /app/entrypoint.sh

EXPOSE 8080
ENTRYPOINT [ "/app/entrypoint.sh" ]
