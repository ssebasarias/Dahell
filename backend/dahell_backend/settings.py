"""
Django settings for dahell_backend project.
"""
from pathlib import Path
import os
import environ

# Initialise environment variables
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent

# .env loading pivot
try:
    env_path = os.path.join(BASE_DIR.parent, '.env')
    print(f"DEBUG: Loading .env from {env_path}")
    with open(env_path, encoding='utf-8') as f:
        environ.Env.read_env(f)
except Exception as e:
    print(f"DEBUG: Error loading .env utf-8: {e}")
    try:
        # Fallback to default loading (system encoding)
        print(f"DEBUG: Attempting to load .env with system encoding from {os.path.join(BASE_DIR.parent, '.env')}")
        environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))
    except Exception as e2:
        print(f"DEBUG: Error loading .env legacy: {e2}")

SECRET_KEY = env('SECRET_KEY', default='django-insecure-wwjbiw8bz)!cc3ec&dq2fqe486=3go)za3+l_bq-n^!ttvbfj(')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', 'backend', 'dahell_backend']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dahell_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dahell_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB', default='dahell_db'),
        'USER': env('POSTGRES_USER', default='dahell_admin'),
        'PASSWORD': env('POSTGRES_PASSWORD', default='secure_password_123'),
        'HOST': env('POSTGRES_HOST', default='127.0.0.1'),
        'PORT': env('POSTGRES_PORT', default='5433'),
        'CONN_MAX_AGE': 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]
CORS_ALLOW_ALL_ORIGINS = DEBUG
