FROM nginx:1.25-alpine

# Loại bỏ config default của nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copy cấu hình Nginx tùy chỉnh
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
