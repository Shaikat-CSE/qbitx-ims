# QBITX IMS (Inventory Management System)

Production-ready Django REST + Nginx + Gunicorn deployment for Hostinger VPS.

## Features
- Django 5.x, REST API, CORS, Token Auth
- SQLite (easy to switch to PostgreSQL/MySQL)
- Static/media served via Nginx
- Environment-based secrets/config
- Example Gunicorn and Nginx configs for subpath deployment

## Deployment Steps

1. **Clone the repo:**
   ```sh
   git clone https://github.com/Shaikat-CSE/qbitx-ims.git
   cd qbitx-ims
   ```
2. **Copy and edit environment/config files:**
   ```sh
   cp .env.example .env
   # Edit .env for your secrets and settings
   cp gunicorn_imstransform.service.example gunicorn_imstransform.service
   cp nginx_django_ims_port8080.conf.example nginx_django_ims_port8080.conf
   ```
3. **Deploy using the script:**
   ```sh
   bash deploy_imstransform.sh
   ```
4. **(On VPS) Enable Gunicorn and Nginx configs:**
   - Copy `gunicorn_imstransform.service` to `/etc/systemd/system/`
   - Copy `nginx_django_ims_port8080.conf` to `/etc/nginx/sites-available/` and symlink to `sites-enabled/`
   - Reload/restart services as needed

## Security Notes
- Never commit `.env` or real secrets to the repo.
- Restrict CORS in production.
- Use HTTPS in production.

## For Developers
- All config templates are provided as `.example` files.
- See `deploy_imstransform.sh` for the full deployment workflow.

---

For more details, see comments in `settings.py` and the deployment script.
