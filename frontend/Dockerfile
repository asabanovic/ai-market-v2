FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (need devDeps for build)
RUN npm ci

# Copy source
COPY . .

# Build the application
RUN npm run build

# Fix Nitro static asset path bug: it generates "../public" but needs "../../../public"
# Create symlink from chunks/public -> ../../public (which resolves to .output/public from chunks/)
RUN ln -sf ../../public .output/server/chunks/public

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
