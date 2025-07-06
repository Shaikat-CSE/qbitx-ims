# Deployment Guide for qbitx-ims

This guide explains how to deploy the qbitx-ims project to a Hostinger VPS that already has other websites running.

## Prerequisites

- A Hostinger VPS with root access
- Your project code in a GitHub repository
- Domain name (optional)

## Deployment Steps

### 1. Clone the Repository to Your Local Machine

If you haven't already, clone the repository to your local machine:

```bash
git clone YOUR_GITHUB_REPO_URL
cd qbitx-ims
```

### 2. Update the deploy.sh Script

Open the `deploy.sh` script and replace `YOUR_GITHUB_REPO_URL` with your actual GitHub repository URL.

### 3. Connect to Your VPS

```bash
ssh root@69.62.75.219
```

### 4. Create Deployment Directory

```bash
mkdir -p /var/www/imstransform
```

### 5. Clone the Repository on the VPS

```bash
cd /var/www/imstransform
git clone YOUR_GITHUB_REPO_URL .
```

### 6. Run the Deployment Script

```bash
cd qbitx-ims
chmod +x deploy.sh
./deploy.sh
```

This script will:
- Update the system
- Install required packages
- Set up a Python virtual environment
- Install project dependencies
- Configure Nginx
- Set up Gunicorn as a systemd service
- Collect static files
- Apply database migrations
- Create a superuser (admin/5254)

### 7. Access Your Application

After successful deployment, your application will be accessible at:

```
http://69.62.75.219/imstransform
```

Admin login:
- Username: admin
- Password: 5254

## Troubleshooting

### Check Gunicorn Status

```bash
systemctl status gunicorn-imstransform
```

### View Gunicorn Logs

```bash
tail -f /var/log/gunicorn/imstransform_error.log
```

### Check Nginx Status

```bash
systemctl status nginx
```

### View Nginx Logs

```bash
tail -f /var/log/nginx/error.log
```

### Restart Services

If you need to restart the services:

```bash
systemctl restart gunicorn-imstransform
systemctl restart nginx
```

## Using a Custom Domain

If you want to use a custom domain instead of the IP address:

1. Update the Nginx configuration file at `/etc/nginx/sites-available/imstransform`:
   - Change `server_name 69.62.75.219;` to `server_name yourdomain.com;`

2. Update the Django settings file:
   - Add your domain to `ALLOWED_HOSTS`
   - Add your domain to `CSRF_TRUSTED_ORIGINS`

3. Restart Nginx:
   ```bash
   systemctl restart nginx
   ```

4. Set up DNS records for your domain to point to your VPS IP address. 