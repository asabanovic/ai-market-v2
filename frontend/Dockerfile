FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Build the application
RUN npm run build

# Verify build output exists
RUN ls -la .output/ && ls -la .output/public/_nuxt/ | head -20

# Create symlink to fix path resolution issue
RUN mkdir -p .output/server/chunks && \
    ln -s ../../public .output/server/chunks/public

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
