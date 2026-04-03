"""
Celery tasks for screenshot processing.
Handles compression, thumbnail generation, and upload to MinIO.
"""

from app.tasks.celery_app import celery_app


@celery_app.task(name="process_screenshot", bind=True, max_retries=3)
def process_screenshot(self, screenshot_id: str, file_data: bytes | None = None):
    """
    Process an uploaded screenshot:
    1. Compress to target quality
    2. Generate thumbnail (320x180)
    3. Upload both to MinIO
    4. Update screenshot record with file paths
    """
    try:
        # TODO: Implement in Milestone 3
        # from PIL import Image
        # from io import BytesIO
        # import boto3

        print(f"Processing screenshot {screenshot_id}")
        return {"status": "processed", "screenshot_id": screenshot_id}

    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@celery_app.task(name="cleanup_old_screenshots")
def cleanup_old_screenshots(retention_days: int = 90):
    """
    Delete screenshots older than retention period.
    Runs daily via Celery Beat.
    """
    # TODO: Implement in Milestone 3
    print(f"Cleaning up screenshots older than {retention_days} days")
    return {"status": "completed"}
