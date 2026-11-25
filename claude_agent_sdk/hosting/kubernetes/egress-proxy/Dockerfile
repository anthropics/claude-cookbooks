# Egress proxy: TLS-terminating nginx that ONLY forwards to api.anthropic.com.
# Plain http{} reverse-proxy — no stream module needed.
FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 443 80

CMD ["nginx", "-g", "daemon off;"]
