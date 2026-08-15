# Multi-stage build for optimized production Next.js application
# Stage 1: Builder - Installs dependencies and builds the app
# Stage 2: Runner - Minimal production image with only necessary files

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────────────────────────────────────────

FROM node:20-alpine AS builder

WORKDIR /app

# Set build environment variables
ENV NODE_ENV=production

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
# Using npm ci for reproducible installs (recommended for CI/CD)
RUN npm ci

# Copy source code
COPY . .

# Build Next.js application
# This generates the .next directory with optimized production build
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runner (Production)
# ─────────────────────────────────────────────────────────────────────────────

FROM node:20-alpine

WORKDIR /app

# Set environment variables for production
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=1024"

# Create app user for security (don't run as root)
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy only necessary files from builder stage
# This results in a much smaller final image
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/next.config.ts ./next.config.ts

# Switch to nextjs user
USER nextjs

# Expose the default Next.js port
# Port can be overridden with environment variable
EXPOSE 3000

# Health check configuration
# Verify the application is responding to requests
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Start the Next.js production server
# 'npm start' is equivalent to 'next start' and handles the production server
CMD ["npm", "start"]
