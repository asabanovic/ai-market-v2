FROM node:18-alpine

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

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

CMD ["npm", "run", "start"]
