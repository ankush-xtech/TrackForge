"""
Celery tasks for report generation.
"""

from app.tasks.celery_app import celery_app


@celery_app.task(name="generate_daily_report")
def generate_daily_report(organization_id: str, date: str):
    """Generate daily activity report for an organization."""
    # TODO: Implement in Milestone 4
    print(f"Generating daily report for org {organization_id} on {date}")
    return {"status": "generated"}


@celery_app.task(name="generate_invoice_pdf")
def generate_invoice_pdf(invoice_id: str):
    """Generate PDF for an invoice."""
    # TODO: Implement in Milestone 6
    print(f"Generating PDF for invoice {invoice_id}")
    return {"status": "generated"}
