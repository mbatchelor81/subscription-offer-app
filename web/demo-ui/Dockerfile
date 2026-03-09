# ============================================================
# demo-ui  —  multi-stage production Dockerfile
# ============================================================
# Runtime environment variables:
#   NEXT_PUBLIC_API_URL – Backend API URL (baked at build time)
# ============================================================

# ---------- Stage 1: install dependencies ----------
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts || npm install --ignore-scripts

# ---------- Stage 2: build ----------
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the Next.js standalone application
RUN npm run build

# ---------- Stage 3: production ----------
FROM node:20-alpine AS production

LABEL maintainer="demo-ui"

# Create a non-root user
RUN addgroup --gid 1001 --system appuser \
    && adduser --uid 1001 --system --ingroup appuser appuser

WORKDIR /app

# Copy only the standalone output and static assets
COPY --from=builder --chown=appuser:appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser:appuser /app/.next/static ./.next/static
# Copy public assets if they exist (the directory may not be present)
COPY --from=builder --chown=appuser:appuser /app/public* ./public/

# Switch to non-root user
USER appuser

EXPOSE 3000

ENV PORT=3000 \
    HOSTNAME="0.0.0.0" \
    NODE_ENV=production

CMD ["node", "server.js"]
