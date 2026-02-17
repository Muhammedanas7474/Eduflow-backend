import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses_client = boto3.client("ses")

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@eduflow.com")


def lambda_handler(event, context):
    """
    Triggered by SQS.
    Expected event structure:
    {
      "Records": [
        {
          "body": "{\"event_type\": \"enrollment_approved\", \"email\": \"...\", \"payload\": {...}}"
        }
      ]
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            event_type = body.get("event_type")

            if event_type == "enrollment_approved":
                send_enrollment_email(body)
            else:
                logger.info(f"Skipping unhandled event type: {event_type}")

        except Exception as e:
            logger.error(f"Error processing record: {e}")
            # Raise exception to trigger SQS retry (DLQ logic)
            raise e

    return {"statusCode": 200, "body": "Processed"}


def send_enrollment_email(data):
    recipient_email = data.get("email")
    payload = data.get("payload", {})
    course_name = payload.get("course_name", "Course")
    student_name = payload.get("student_name", "Student")

    if not recipient_email:
        logger.warning("No recipient email found.")
        return

    subject = f"Enrollment Approved: {course_name}"

    body_text = f"""
    Dear {student_name},

    Congratulations! Your enrollment for the course "{course_name}" has been approved by the instructor.

    You can now access the course content on your dashboard.

    Happy Learning!
    The EduFlow Team
    """

    body_html = f"""
    <html>
    <head></head>
    <body>
      <h2>Enrollment Approved</h2>
      <p>Dear {student_name},</p>
      <p>Congratulations! Your enrollment for the course <strong>{course_name}</strong> has been approved by the instructor.</p>
      <p>You can now access the course content on your dashboard.</p>
      <br>
      <p>Happy Learning!</p>
      <p>The EduFlow Team</p>
    </body>
    </html>
    """

    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
        logger.info(
            f"Email sent to {recipient_email}. MessageId: {response['MessageId']}"
        )

    except Exception as e:
        logger.error(f"Failed to send email via SES: {e}")
        raise e
