# NOTA: Envia e-mails por SMTP. Sem SMTP configurado, só registra no log e na lista OUTBOX (usada em desenvolvimento e testes).

"""Transactional e-mail over plain SMTP (works with Resend, SendGrid, Amazon SES, Gmail...).

Without SMTP_HOST the message is only logged and kept in OUTBOX, so development and tests
work without a provider. Sending never raises: a failed e-mail must not break the request.
"""

import asyncio
import logging
import os
import smtplib
from collections import deque
from email.message import EmailMessage

log = logging.getLogger("techconnect.mail")

OUTBOX: deque = deque(maxlen=200)
APP_URL = os.getenv("APP_URL", "http://localhost:5173").rstrip("/")


def _send_sync(msg: EmailMessage) -> None:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user, password = os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        server = smtplib.SMTP(host, port, timeout=20)
        server.starttls()
    with server:
        if user:
            server.login(user, password)
        server.send_message(msg)


async def send_email(to: str, subject: str, text: str) -> None:
    OUTBOX.append({"to": to, "subject": subject, "text": text})
    if not os.getenv("SMTP_HOST"):
        log.info("E-mail (SMTP não configurado) para %s: %s", to, subject)
        return
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM", "TechConnect <nao-responda@techconnect.com.br>")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text + "\n\n— TechConnect 2.0")
    try:
        await asyncio.to_thread(_send_sync, msg)
    except Exception as e:  # noqa: BLE001 - delivery problems are logged, never surfaced to the user
        log.warning("Falha ao enviar e-mail para %s: %s", to, e.__class__.__name__)
