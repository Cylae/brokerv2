#!/bin/bash

# ======================================================
# AI Trading System - Automated Security Setup
# Installs Nginx, Configures Reverse Proxy, Enables SSL
# ======================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

DOMAIN=$1
PORT=8501 # Default Streamlit Port

if [ -z "$DOMAIN" ]; then
    echo "Usage: sudo ./setup_ssl.sh <your-domain.com>"
    exit 1
fi

echo "--- Installing Dependencies ---"
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

echo "--- Configuring Nginx for $DOMAIN ---"
cat > /etc/nginx/sites-available/$DOMAIN <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx Config
nginx -t

# Reload Nginx
systemctl reload nginx

echo "--- Obtaining SSL Certificate (LetsEncrypt) ---"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN --redirect

echo "--- Success! ---"
echo "Your dashboard should now be accessible at https://$DOMAIN"
echo "Don't forget to configure DASHBOARD_USERNAME and DASHBOARD_PASSWORD in .env!"
