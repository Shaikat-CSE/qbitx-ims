# QBITX IMS Transform Suppliers

A Django-based Inventory Management System (IMS) for suppliers and clients, with a modern frontend and REST API.

## Features
- Product, stock, supplier, and client management
- Custom reports and export (CSV, Excel, PDF)
- Role-based permissions
- Responsive Bootstrap 5 frontend
- Token-based authentication (DRF)

## Deployment: VPS at `/imstransform`

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd django_ims
```

### 2. Configure Django Settings
- Edit `ims_project/settings.py`:
  - `ALLOWED_HOSTS = ['69.62.75.219', 'localhost', '127.0.0.1']`
  - `FORCE_SCRIPT_NAME = '/imstransform'`
  - `STATIC_URL = '/imstransform/static/'`
  - `MEDIA_URL = '/imstransform/media/'`
  - `STATIC_ROOT = BASE_DIR / 'staticfiles'`
  - `MEDIA_ROOT = BASE_DIR / 'media'`

### 3. Install System Dependencies
```sh
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-venv python3-pip git nginx -y
```

### 4. Automated Deployment
Run the provided script:
```sh
chmod +x deploy_imstransform.sh
./deploy_imstransform.sh
```
- This will set up the virtual environment, install requirements, collect static files, run migrations, configure Gunicorn and Nginx, and open port 8080.

### 5. Access the Application
- Visit: [http://69.62.75.219:8080/imstransform](http://69.62.75.219:8080/imstransform)

### 6. Default Admin
- Create a superuser if needed:
```sh
source venv/bin/activate
python manage.py createsuperuser
```
- Admin panel: `/imstransform/admin/`

### 7. Notes
- All frontend and API URLs must be prefixed with `/imstransform/`.
- For production, ensure `DEBUG = False` and use strong, secret keys.
- For HTTPS, set up SSL with Nginx and update the server config.

---

## Project Structure
```
django_ims/
├── ims_project/           # Django project settings
├── inventory/             # Main app
├── frontend/              # HTML, JS, CSS
├── staticfiles/           # Collected static files
├── media/                 # Uploaded media files
├── requirements.txt
├── deploy_imstransform.sh # Automated deployment script
├── gunicorn.service.example
├── nginx_django_ims_port8080.conf.example
└── README.md
```

## License
MIT (or your chosen license)
# qbitx-ims
