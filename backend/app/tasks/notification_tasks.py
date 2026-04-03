"""
Celery tasks for sending notifications (email, webhooks).
"""

from app.tasks.celery_app import celery_app


@celery_app.task(name="send_email")
def send_email(to_email: str, subject: str, html_body: str):
    """Send an email notification."""
    # TODO: Implement with SMTP in Milestone 2
    print(f"Sending email to {to_email}: {subject}")
    return {"status": "sent", "to": to_email}


@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_id: str, email: str):
    """Send welcome email to newly registered user."""
    print(f"Sending welcome email to {email}")
    return {"status": "sent"}
