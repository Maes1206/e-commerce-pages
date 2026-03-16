import os
import smtplib
from email.message import EmailMessage

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from dotenv import load_dotenv


load_dotenv()


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str) -> list[str]:
    value = os.getenv(name, "*").strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


app = FastAPI(title="Restaurant Contact API")

cors_origins = env_list("CONTACT_API_CORS_ORIGINS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if cors_origins == ["*"] else cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/contact")
def send_contact(
    name: str = Form(...),
    mail: EmailStr = Form(...),
    comment: str = Form(...),
    website: str = Form(""),
    subject: str = Form(""),
) -> dict[str, str]:
    name = name.strip()
    comment = comment.strip()
    website = website.strip()
    subject = subject.strip()

    if not name:
        return {"info": "error", "msg": "Please enter your name."}
    if not comment:
        return {"info": "error", "msg": "Please enter your message."}

    to_email = os.getenv("CONTACT_TO_EMAIL", "").strip()
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username or to_email).strip()
    subject_prefix = os.getenv("CONTACT_SUBJECT_PREFIX", "Restaurant Website = From:").strip()
    use_tls = env_flag("SMTP_USE_TLS", True)
    use_ssl = env_flag("SMTP_USE_SSL", False)

    if not to_email or not smtp_host or not smtp_from_email:
        raise HTTPException(
            status_code=500,
            detail="SMTP is not configured. Set CONTACT_TO_EMAIL, SMTP_HOST and SMTP_FROM_EMAIL.",
        )

    message = EmailMessage()
    message["Subject"] = f"{subject_prefix} {name}".strip()
    message["From"] = smtp_from_email
    message["To"] = to_email
    message["Reply-To"] = str(mail)
    message.set_content(
        "\n".join(
            [
                f"Name: {name}",
                f"E-mail: {mail}",
                f"Website: {website or '-'}",
                f"Subject: {subject or '-'}",
                "",
                "Comment:",
                comment,
            ]
        )
    )

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                if smtp_username:
                    server.login(smtp_username, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                if use_tls:
                    server.starttls()
                    server.ehlo()
                if smtp_username:
                    server.login(smtp_username, smtp_password)
                server.send_message(message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to send message: {exc}") from exc

    return {"info": "success", "msg": "Your message has been sent. Thank you!"}
