# --------------------------------------------------------
# STAGE 1: THE BUILDER
# --------------------------------------------------------
# THE MAGIC: We force this stage to ALWAYS run on the Robot's native CPU 
# (AMD64), even if we are building the final image for Apple Silicon.
# This makes 'npm run build' run at 100% speed.
FROM --platform=$BUILDPLATFORM node:16-bookworm AS builder
WORKDIR /app
COPY package.json yarn.lock ./
# Install dependencies
RUN npm install
COPY . .
# Build the DLL and the Production Dist
RUN npm run build:dll
RUN npm run build

# Stage 2: The Server (Nginx)
FROM nginx:alpine
# Copy the built "Candy" from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy the config file
COPY deploy/nginx.conf /etc/nginx/nginx.conf
# Nginx runs automatically