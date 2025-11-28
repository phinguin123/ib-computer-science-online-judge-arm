# Use Node 16 which is stable on ARM64
# FIX: Switched from 'buster' to 'bookworm' for consistency and better ARM64 support
FROM node:16-bookworm AS builder

WORKDIR /app
COPY package.json yarn.lock ./

# Install dependencies
RUN npm install

COPY . .

# Build the DLL and the production assets
ENV NODE_ENV=production
RUN npm run build:dll
RUN npm run build

# We don't need a CMD here because we will copy the files out in the Backend Dockerfile
