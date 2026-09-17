import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    anthropic_api_key: str = ""
    resend_api_key: str = ""
    founder_email: str = ""
    regression_tolerance: float = 0.10
    observability_port: int = 8095
    demo_mode: bool = True
    redaction_enabled: bool = True
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            resend_api_key=os.getenv("RESEND_API_KEY", ""),
            founder_email=os.getenv("FOUNDER_EMAIL", ""),
            regression_tolerance=float(os.getenv("REGRESSION_TOLERANCE", "0.10")),
            observability_port=int(os.getenv("OBSERVABILITY_PORT", "8095")),
            demo_mode=os.getenv("DEMO_MODE", "false").lower() == "true",
            redaction_enabled=os.getenv("REDACTION_ENABLED", "true").lower() == "true",
            api_key=os.getenv("OBSERVABILITY_API_KEY", ""),
        )

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


def get_settings() -> Settings:
    return Settings.from_env()
