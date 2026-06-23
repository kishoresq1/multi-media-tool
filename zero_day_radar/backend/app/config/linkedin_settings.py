from pydantic_settings import BaseSettings, SettingsConfigDict


class LinkedInSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8009/auth/linkedin/callback"
    linkedin_organization_id: str | None = None
    linkedin_api_version: str = "202506"
    linkedin_scopes: str = "openid profile w_member_social"
    linkedin_post_mode: str = "member"  # member | organization
    frontend_url: str = "http://localhost:5173"
    session_secret: str = "change-me"


linkedin_settings = LinkedInSettings()
