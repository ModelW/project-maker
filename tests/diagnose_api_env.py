"""
Shows how a generated API's settings see their environment: which .env gets
loaded, the database URL they receive and what the preset makes of it. Run
from the API's folder, with its venv (see the start test, which uses it when
the API fails to start).
"""

import os
import re
import sys
from pathlib import Path

import model_w.env_manager._dotenv as dotenv

original_find_dotenv = dotenv.find_dotenv


def find_dotenv(*args, **kwargs):
    found = original_find_dotenv(*args, **kwargs)
    print("find_dotenv:", found)
    return found


def main():
    dotenv.find_dotenv = find_dotenv
    sys.path.insert(0, os.getcwd())

    manage = Path("manage.py").read_text(encoding="utf-8")
    settings_module = re.search(r'"(\w+\.django\.settings)"', manage).group(1)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    import django
    from django.conf import settings

    django.setup()

    url = os.environ.get("DATABASE_URL") or ""
    print("DATABASE_URL:", url.split("@")[-1])
    print("DATABASES:", {k: sorted(v) for k, v in settings.DATABASES.items()})

    from model_w.env_manager import EnvManager
    from model_w.preset.django import ModelWDjango

    env = EnvManager()
    env.load_dotenv()

    try:
        out = list(ModelWDjango().pre_database(env) or [])
        print("pre_database:", [(k, sorted(v["default"])) for k, v in out])
    except Exception as e:  # noqa: BLE001 (it's a diagnostic)
        print("pre_database failed:", repr(e))

    print("env errors:", env.missing, env.syntax_error, env.signature_mismatch)


if __name__ == "__main__":
    main()
