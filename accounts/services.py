import logging

from django.conf import settings
from django.template import loader
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_mail_sendpulse(subject, email_template_name, context, email_to, name_to=""):
    try:
        from pysendpulse.pysendpulse import PySendPulse
    except ImportError as exc:
        raise RuntimeError(
            "Biblioteca pysendpulse nao instalada. Instale com: pip install pysendpulse"
        ) from exc

    if not settings.CLIENT_ID_SENDPULSE or not settings.CLIENT_SECRET_SENDPULSE:
        raise RuntimeError("Defina CLIENT_ID_SENDPULSE e CLIENT_SECRET_SENDPULSE no ambiente.")

    sp_api_proxy = PySendPulse(settings.CLIENT_ID_SENDPULSE, settings.CLIENT_SECRET_SENDPULSE)

    html_content = loader.render_to_string(email_template_name, context)
    text_content = strip_tags(html_content)

    email = {
        "subject": subject,
        "html": html_content,
        "text": text_content,
        "from": {"name": settings.SENDPULSE_FROM_NAME, "email": settings.DEFAULT_FROM_EMAIL},
        "to": [{"name": name_to, "email": email_to}],
    }

    response = sp_api_proxy.smtp_send_mail(email)
    error = response.get("data") if isinstance(response, dict) else None

    if (
        isinstance(response, dict)
        and (response.get("is_error") or response.get("result") is False)
    ):
        raise RuntimeError(f"SendPulse rejected the email: {response}")

    if isinstance(error, dict) and error.get("is_error"):
        message = error.get("message") or response
        raise RuntimeError(f"SendPulse rejected the email: {message}")

    logger.info(
        "SendPulse email accepted for delivery to %s with id %s",
        email_to,
        response.get("id") if isinstance(response, dict) else None,
    )
    return response

