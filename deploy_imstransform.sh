#!/bin/bash

# === CONFIGURATION ===
PROJECT_NAME="django_ims"
VPS_USER="root"
VPS_IP="69.62.75.219"
DJANGO_DIR="/home/$VPS_USER/$PROJECT_NAME"
PYTHON_BIN="python3"
VENV_DIR="$DJANGO_DIR/venv"
GUNICORN_SERVICE="gunicorn"
NGINX_CONF_SRC="$DJANGO_DIR/nginx_django_ims_port8080.conf.example"
NGINX_CONF_DEST="/etc/nginx/sites-available/${PROJECT_NAME}_8080"

# === SYSTEM UPDATE & DEPENDENCIES ===
echo "[1/7] Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install $PYTHON_BIN $PYTHON_BIN-venv $PYTHON_BIN-pip git nginx -y

# === SETUP PROJECT ===
echo "[2/7] Setting up project..."
cd $DJANGO_DIR || { echo "Project directory not found!"; exit 1; }

# Set up virtual environment
$PYTHON_BIN -m venv venv
source $VENV_DIR/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# === DJANGO SETTINGS ===
echo "[3/7] Checking Django settings..."
echo "ALLOWED_HOSTS, FORCE_SCRIPT_NAME, STATIC_URL, MEDIA_URL should be set for /imstransform."
read -p "Press [Enter] to continue after confirming settings.py..."

# Collect static files and migrate
echo "[4/7] Collecting static files and running migrations..."
$PYTHON_BIN manage.py collectstatic --noinput
$PYTHON_BIN manage.py migrate

# === GUNICORN SYSTEMD SERVICE ===
echo "[5/7] Setting up Gunicorn systemd service..."
sudo cp gunicorn.service.example /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn

# === NGINX CONFIGURATION ===
echo "[6/7] Configuring Nginx..."
sudo cp $NGINX_CONF_SRC $NGINX_CONF_DEST
sudo ln -sf $NGINX_CONF_DEST /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# === FIREWALL ===
echo "[7/7] Allowing port 8080 through firewall..."
sudo ufw allow 8080

# === DONE ===
echo "Deployment complete!"
echo "Visit: http://$VPS_IP:8080/imstransform" 