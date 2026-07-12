FROM node:20-slim AS builder

# Build context is the repo root (see docker-compose.yml) so the Next.js build
# can resolve `../../../../data/fixtures/*.json` imports the same way it does
# in local dev, where frontend/ and data/ are sibling directories.
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend .
COPY data /app/data
RUN npm run build

FROM node:20-slim

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/frontend/public ./public
COPY --from=builder /app/frontend/.next ./.next
COPY --from=builder /app/frontend/node_modules ./node_modules
COPY --from=builder /app/frontend/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
