FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci --frozen-lockfile

# Sao chép toàn bộ mã nguồn của ReactJS
COPY . .

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Nginx Production chạy bên trong Container mặc định ở cổng 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]