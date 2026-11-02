"""Create a local .env with a freshly generated secret key. Run once: python scripts/init_dev_env.py"""
import secrets
from pathlib import Path

env = Path(__file__).resolve().parent.parent / ".env"
if env.exists():
    print(".env already exists - leaving it unchanged.")
else:
    env.write_text(
        f"DJANGO_SECRET_KEY={secrets.token_urlsafe(50)}\n"
        "DJANGO_DEBUG=true\n"
        "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1\n",
        encoding="utf-8",
    )
    print("Created .env (local only, gitignored). Do not share or commit it.")
