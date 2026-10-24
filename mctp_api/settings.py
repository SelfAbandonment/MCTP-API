"""
Django settings for mctp_api project.

Project settings for the Django 6.0 API backend.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths relative to the repository root.
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


# Load local development variables when a .env file is present.
load_dotenv(BASE_DIR / ".env")

# Development defaults; production values must be supplied through the environment.
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the production secret key secret.
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-key"
    else:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required when DEBUG is false")

_allowed_hosts_default = "localhost,127.0.0.1,.onrender.com"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", _allowed_hosts_default).split(",") if host.strip()]


# Application definition

INSTALLED_APPS = [
    # Admin
    "unfold",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Authentication (allauth)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.headless",
    "mctp_api.auth.microsoft_provider",
    # Api
    "rest_framework_simplejwt.token_blacklist",
    # Third-party apps
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # Project apps (mctp_api_core last so its admin customization can
    # unregister/re-register the admin classes from the apps above)
    "mctp_api.auth",
    "mctp_api.community",
    "mctp_api.mctp_api_core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

ROOT_URLCONF = "mctp_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mctp_api.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================== Django REST Framework ====================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "EXCEPTION_HANDLER": "mctp_api.mctp_api_core.exceptions.custom_exception_handler",
}


# ==================== JWT configuration ====================

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ==================== CORS configuration ====================

CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-session-token",
    "x-email-verification-key",
    "x-password-reset-key",
)

# Microsoft OAuth callback (headless allauth) is same-site in local development;
# GitHub Pages cross-site cookies require SameSite=None + Secure or a same-site
# frontend proxy. Keep Lax for localhost and revisit at deployment time.
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


# ==================== OpenAPI configuration (drf-spectacular) ====================

SPECTACULAR_SETTINGS = {
    "TITLE": "MCTP API",
    "DESCRIPTION": "MCTP Project Backend RESTful API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}


# ==================== Microsoft OAuth / Minecraft configuration ====================
# The allauth provider callback is /accounts/microsoft/login/callback/ (Azure App
# Registration redirect URI). MS_REDIRECT_URI from the legacy custom flow is no
# longer used.

MS_CLIENT_ID = _env_first("MS_CLIENT_ID", "MS_OAUTH_CLIENT_ID")
MS_CLIENT_SECRET = _env_first("MS_CLIENT_SECRET", "MS_OAUTH_CLIENT_SECRET")
FRONTEND_OAUTH_CALLBACK = os.getenv(
    "FRONTEND_OAUTH_CALLBACK",
    "http://localhost:5173/#/auth/microsoft/callback",
)
# Fernet key for encrypting Microsoft refresh tokens at rest. Generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
MS_TOKEN_FERNET_KEY = _env_first("MS_TOKEN_FERNET_KEY", "MS_REFRESH_TOKEN_FERNET_KEY")

if not DEBUG and (MS_CLIENT_ID or MS_CLIENT_SECRET) and not MS_TOKEN_FERNET_KEY:
    raise ImproperlyConfigured("MS_TOKEN_FERNET_KEY is required when Microsoft OAuth is enabled")

# ==================== django-allauth (headless + Microsoft/Minecraft) ====================
# The account system is owned by allauth. Headless browser endpoints are used by
# the Vue SPA (local development: same-site localhost); the SPA exchanges the
# allauth session for a short-lived SimpleJWT pair through
# POST /api/v1/auth/token/session/ so the existing API keeps using Bearer JWT.

HEADLESS_ONLY = True
HEADLESS_CLIENTS = ("browser",)

ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

SOCIALACCOUNT_ADAPTER = "mctp_api.auth.adapters.MCTPSocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = False
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_PROVIDERS = {
    "microsoft": {
        "APP": {
            "client_id": MS_CLIENT_ID,
            "secret": MS_CLIENT_SECRET,
        },
        "SCOPE": ["XboxLive.signin", "offline_access"],
        "AUTH_PARAMS": {"prompt": "select_account"},
        # The custom provider uses login.live.com (consumer endpoint). Azure app
        # registration must allow personal Microsoft accounts and the
        # XboxLive.signin scope.
        "OAUTH_PKCE_ENABLED": False,
    }
}

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
HEADLESS_FRONTEND_URLS = {
    "socialaccount_login_error": FRONTEND_OAUTH_CALLBACK,
    "account_confirm_email": f"{FRONTEND_BASE_URL}/#/account/verify-email/{{key}}",
    "account_reset_password_from_key": f"{FRONTEND_BASE_URL}/#/account/password/reset/key/{{key}}",
    "account_signup": f"{FRONTEND_BASE_URL}/#/register",
}

# allauth's provider callback URL is /accounts/microsoft/login/callback/.
# Keep this in sync with the Azure app registration redirect URI.
ALLAUTH_MICROSOFT_CALLBACK_PATH = "/accounts/microsoft/login/callback/"


# ==================== django-unfold admin ====================

UNFOLD = {
    "SITE_TITLE": "MCTP 管理后台",
    "SITE_HEADER": "MCTP · 方块社区",
    "SITE_SUBHEADER": "社区运营与玩家管理",
    "SITE_URL": os.getenv("FRONTEND_BASE_URL", "/"),
    "INDEX_TITLE": "运营概览",
    "THEME": "dark",
    "DASHBOARD_CALLBACK": "mctp_api.mctp_api_core.dashboard.dashboard_callback",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_LANGUAGES": False,
    "SITE_ICON": "/static/admin/mctp-icon.svg",
    "SITE_FAVICONS": [
        {"rel": "icon", "type": "image/svg+xml", "href": "/static/admin/mctp-icon.svg"},
    ],
    "STYLES": ["/static/admin/mctp-admin.css"],
    "COLORS": {
        "primary": {
            "50": "#f2fde8",
            "100": "#e0fbc9",
            "200": "#c4f79c",
            "300": "#9fef68",
            "400": "#7fe143",
            "500": "#8ce06a",
            "600": "#62b83f",
            "700": "#4b9130",
            "800": "#3d722a",
            "900": "#345e27",
            "950": "#19350f",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "社区运营",
                "separator": False,
                "items": [
                    {"title": "公告", "icon": "campaign", "link": "/admin/community/announcement/"},
                    {"title": "玩家", "icon": "person", "link": "/admin/auth/user/"},
                    {"title": "用户组", "icon": "group", "link": "/admin/auth/group/"},
                ],
            },
            {
                "title": "账户与绑定",
                "separator": True,
                "items": [
                    {"title": "微软绑定", "icon": "link", "link": "/admin/socialaccount/socialaccount/"},
                    {"title": "邮箱", "icon": "mail", "link": "/admin/account/emailaddress/"},
                    {"title": "旧版 MC 绑定", "icon": "history", "link": "/admin/mctp_auth/microsoftaccount/"},
                ],
            },
            {
                "title": "系统",
                "separator": True,
                "items": [
                    {"title": "站点", "icon": "public", "link": "/admin/sites/site/"},
                ],
            },
        ],
    },
}
