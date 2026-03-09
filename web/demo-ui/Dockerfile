# =============================================================================
# demo-ui  —  Production Dockerfile (multi-stage)
# =============================================================================
# Runtime environment variables:
#   NEXT_PUBLIC_API_URL  – Backend API URL (baked at build time)
#   PORT                 – (optional) Override default port 3000
# =============================================================================

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

RUN npm run build

# ---------- Stage 3: production ----------
FROM node:20-alpine AS production

LABEL maintainer="subscription-offer-app"

# Create a non-root user
RUN addgroup --gid 1001 --system appuser \
    && adduser --uid 1001 --system --ingroup appuser appuser

WORKDIR /app

# Copy standalone output from builder
COPY --from=builder --chown=appuser:appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser:appuser /app/.next/static ./.next/static
# Copy public assets if they exist (uncomment when public/ dir is added)
# COPY --from=builder --chown=appuser:appuser /app/public ./public

USER appuser

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
