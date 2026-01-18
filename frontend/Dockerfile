FROM docker.io/oven/bun:1-alpine

WORKDIR /app

# Install dependencies
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

# Copy application
COPY . .

EXPOSE 3000

CMD ["bun", "run", "dev"]
