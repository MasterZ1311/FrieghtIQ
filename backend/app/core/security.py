from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import secrets

def generate_secure_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)
