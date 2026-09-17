from __future__ import annotations

from typing import Iterable

from .models import RegressionAlert


def send_regression_alerts(alerts: Iterable[RegressionAlert], api_key: str = "", founder_email: str = "") -> bool:
    alerts = list(alerts)
    if not alerts or not api_key or not founder_email:
        return False
    try:
        import resend
        resend.api_key = api_key
        summary = "\n".join(
            f"- {a.service} / {a.metric}: {a.baseline:.3f} -> {a.current:.3f} ({a.drop_pct:.1%})"
            for a in alerts
        )
        resend.Emails.send({
            "from": "observability@worldtradefactory.ai",
            "to": founder_email,
            "subject": f"Regression detected in {len({a.service for a in alerts})} service(s)",
            "text": f"Quality regression detected:\n{summary}",
        })
        return True
    except Exception:
        return False
