# Build stage
FROM klakegg/hugo:0.111.3-alpine AS builder

WORKDIR /src
COPY . .

# Generate config.toml from template using environment variable
ARG DOMAIN_NAME=princetonstrong.online
RUN if [ -f config.toml.template ]; then \
      sed "s/\${DOMAIN_NAME}/${DOMAIN_NAME}/g" config.toml.template > config.toml; \
    fi

RUN hugo --minify

# Runtime stage
FROM nginx:1.25-alpine

# Copy Hugo build output to nginx
COPY --from=builder /src/public /usr/share/nginx/html

# Add custom nginx config for SPA routing and metrics
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    # Nginx status for metrics \
    location /nginx_status { \
        stub_status on; \
        access_log off; \
        allow 127.0.0.1; \
        deny all; \
    } \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
