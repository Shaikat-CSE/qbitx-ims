#!/bin/bash

# Exit on error
set -e

# Update system
apt update
apt upgrade -y

# Install required packages (if not already installed)
apt install -y python3-pip python3-venv nginx

# Create project directory
mkdir -p /var/www/imstransform
cd /var/www/imstransform

# Clone the repository (assuming you'll provide the GitHub URL)
# git clone YOUR_GITHUB_REPO_URL .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install project dependencies
pip install -r qbitx-ims/requirements.txt
pip install gunicorn

# Create media directory if it doesn't exist
mkdir -p qbitx-ims/media

# Create log directory for Gunicorn
mkdir -p /var/log/gunicorn
chmod 755 /var/log/gunicorn

# Collect static files
cd qbitx-ims
python manage.py collectstatic --noinput

# Apply migrations
python manage.py migrate

# Create superuser
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'shaikat143@gmail.com', '5254') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Set up Nginx - careful not to disrupt existing sites
cp nginx.conf /etc/nginx/sites-available/imstransform
ln -sf /etc/nginx/sites-available/imstransform /etc/nginx/sites-enabled/
# Don't remove default since there might be other sites
# rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Set up Gunicorn service
cp gunicorn.service /etc/systemd/system/gunicorn-imstransform.service
systemctl daemon-reload
systemctl start gunicorn-imstransform
systemctl enable gunicorn-imstransform

echo "Deployment completed successfully!"
echo "Your application should be accessible at http://69.62.75.219/imstransform"
echo "Admin login: username=admin, password=5254" 