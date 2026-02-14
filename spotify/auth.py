from __future__ import annotations

import json
import os
import secrets
from datetime import UTC, datetime
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from spotipy import SpotifyOAuth
from spotipy.cache_handler import CacheHandler

from db.models import OAuthToken
from db.session import SessionLocal

PROVIDER = "spotify"
OAUTH_STATE_SESSION_KEY = "spotify_oauth_state"

SPOTIFY_SCOPES: tuple[str, ...] = (
    "user-read-recently-played",
    "user-read-currently-playing",
    "user-read-playback-state",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-top-read",
)


class OAuthConfigError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise OAuthConfigError(f"Missing required env var: {name}")
    return value


def _fernet() -> Fernet:
    raw_key = _require_env("FERNET_KEY")
    try:
        return Fernet(raw_key.encode("utf-8"))
    except ValueError as exc:
        raise OAuthConfigError("FERNET_KEY is invalid. Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'") from exc


class EncryptedTokenCacheHandler(CacheHandler):
    def __init__(self, provider: str = PROVIDER) -> None:
        self.provider = provider
        self.cipher = _fernet()

    def get_cached_token(self) -> dict[str, Any] | None:
        with SessionLocal() as session:
            row = session.get(OAuthToken, self.provider)
            if not row:
                return None
            try:
                decrypted = self.cipher.decrypt(row.token_encrypted.encode("utf-8"))
            except InvalidToken:
                return None
            payload = json.loads(decrypted.decode("utf-8"))
            return payload if isinstance(payload, dict) else None

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        encrypted = self.cipher.encrypt(json.dumps(token_info).encode("utf-8")).decode("utf-8")
        with SessionLocal() as session:
            row = session.get(OAuthToken, self.provider)
            now = datetime.now(UTC)
            if row is None:
                row = OAuthToken(provider=self.provider, token_encrypted=encrypted, updated_at=now)
                session.add(row)
            else:
                row.token_encrypted = encrypted
                row.updated_at = now
            session.commit()

    def delete_token_from_cache(self) -> None:
        with SessionLocal() as session:
            row = session.get(OAuthToken, self.provider)
            if row:
                session.delete(row)
                session.commit()


def get_spotify_oauth(state: str | None = None) -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=_require_env("SPOTIFY_CLIENT_ID"),
        client_secret=_require_env("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=_require_env("SPOTIFY_REDIRECT_URI"),
        scope=" ".join(SPOTIFY_SCOPES),
        cache_handler=EncryptedTokenCacheHandler(),
        state=state,
        open_browser=False,
    )


def build_authorize_url(state: str) -> str:
    oauth = get_spotify_oauth(state=state)
    return oauth.get_authorize_url(state=state)


def generate_state_token() -> str:
    return secrets.token_urlsafe(24)


def exchange_code_for_token(code: str, state: str | None = None) -> dict[str, Any]:
    oauth = get_spotify_oauth(state=state)
    try:
        token_info = oauth.get_access_token(code=code, as_dict=True, check_cache=False)
    except TypeError:
        token_info = oauth.get_access_token(code)

    if isinstance(token_info, dict):
        oauth.cache_handler.save_token_to_cache(token_info)
        return token_info
    raise RuntimeError("Spotify OAuth did not return a valid token payload.")


def get_token_info() -> dict[str, Any] | None:
    oauth = get_spotify_oauth()
    return oauth.cache_handler.get_cached_token()


def get_valid_token_info() -> dict[str, Any] | None:
    oauth = get_spotify_oauth()
    token_info = oauth.cache_handler.get_cached_token()
    if not token_info:
        return None
    return oauth.validate_token(token_info)


def is_connected() -> bool:
    return get_valid_token_info() is not None


def disconnect_spotify() -> None:
    handler = EncryptedTokenCacheHandler()
    handler.delete_token_from_cache()
