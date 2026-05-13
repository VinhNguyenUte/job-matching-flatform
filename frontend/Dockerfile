# ==================== FRONTEND - Next.js (Phiên bản ổn định) ====================

FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Cài dependencies
RUN npm ci --frozen-lockfile

# Copy toàn bộ source code
COPY . .

# Build Next.js
RUN npm run build

# Expose port
EXPOSE 3000

# Chạy production
CMD ["npm", "start"]