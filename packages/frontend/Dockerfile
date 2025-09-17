FROM node:18-alpine

WORKDIR /app

# Copy root package files
COPY package.json pnpm-workspace.yaml ./
COPY pnpm-lock.yaml* ./
COPY tsconfig.json ./

# Copy shared package
COPY packages/shared ./packages/shared

# Copy frontend package files
COPY packages/frontend/package.json ./packages/frontend/

# Install pnpm
RUN npm install -g pnpm

# Copy frontend source code first
COPY packages/frontend ./packages/frontend

# Install dependencies
RUN pnpm install --no-frozen-lockfile --filter=frontend...

# Set working directory to frontend
WORKDIR /app/packages/frontend

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership of the app directory
RUN chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000

CMD ["pnpm", "dev"]