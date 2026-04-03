FROM node:20-alpine

WORKDIR /app

# Dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Application code
COPY . .

# Expose port
EXPOSE 3000

# Default: dev mode with hot reload
CMD ["npm", "run", "dev"]
