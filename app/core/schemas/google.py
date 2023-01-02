from pydantic import BaseModel
from datetime import datetime
from google.oauth2.credentials import Credentials as GoogleCredentials


# User
class Credentials(BaseModel):
    token: str
    expiry: datetime
    _quota_project_id: str
    _scopes: str
    _default_scopes: str
    _refresh_token: str
    _id_token: str
    _granted_scopes: str
    _token_uri: str
    _client_id: str
    _client_secret: str
    _rapt_token: str
    _refresh_handler: str
    _enable_reauth_refresh: bool

    @classmethod
    def from_google_credentials(cls, credentials: GoogleCredentials) -> "Credentials":
        return cls(
            token = credentials.token,
            expiry = credentials.expiry,
            _quota_project_id = credentials._quota_project_id,
            _scopes = credentials._scopes,
            _default_scopes = credentials._default_scopes,
            _refresh_token = credentials._refresh_token,
            _id_token = credentials._id_token,
            _granted_scopes = credentials._granted_scopes,
            _token_uri = credentials._token_uri,
            _client_id = credentials._client_id,
            _client_secret = credentials._client_secret,
            _rapt_token = credentials._rapt_token,
            _refresh_handler = credentials._refresh_handler,
            _enable_reauth_refresh = credentials._enable_reauth_refresh
        )
