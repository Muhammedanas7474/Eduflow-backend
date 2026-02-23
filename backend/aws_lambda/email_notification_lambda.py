import json
import logging
import os

import boto3
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 🔹 SES Client
ses = boto3.client("ses", region_name="ap-south-1")

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

# 🔹 Initialize Firebase from ENV VAR → write to /tmp/firebase.json
if not firebase_admin._apps:
    firebase_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if firebase_json:
        with open("/tmp/firebase.json", "w") as f:
            f.write(firebase_json)
        cred = credentials.Certificate("/tmp/firebase.json")
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized from env var")
    else:
        logger.warning("FIREBASE_SERVICE_ACCOUNT env var not set!")


def send_push_notification(token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"Push sent: {response}")
    except Exception as e:
        logger.error(f"Push notification failed: {e}")
        # Don't raise — email was already sent


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    for record in event["Records"]:
        body = json.loads(record["body"])

        event_type = body.get("event_type")
        email = body.get("email")
        payload = body.get("payload", {})
        fcm_token = body.get("fcm_token")

        if event_type == "enrollment_approved":
            course_name = payload.get("course_name", "a course")
            student_name = payload.get("student_name", "Student")

            title = "🎓 Enrollment Approved"
            message_text = f"You are enrolled in {course_name}"

            # 1️⃣ Send Email via SES
            try:
                ses.send_email(
                    Source=f"EduFlow <{SENDER_EMAIL}>",
                    Destination={"ToAddresses": [email]},
                    Message={
                        "Subject": {"Data": title},
                        "Body": {
                            "Text": {"Data": message_text},
                            "Html": {
                                "Data": f"""
                                <html>
                                <body>
                                <h2>Enrollment Approved</h2>
                                <p>Dear {student_name},</p>
                                <p>Your enrollment for <strong>{course_name}</strong> has been approved!</p>
                                <p>You can now access the course on your dashboard.</p>
                                <br>
                                <p>Happy Learning!<br>The EduFlow Team</p>
                                </body>
                                </html>
                                """
                            },
                        },
                    },
                )
                logger.info(f"Email sent to {email}")
            except Exception as e:
                logger.error(f"Email failed: {e}")
                raise e

            # 2️⃣ Send Push via FCM
            if fcm_token:
                send_push_notification(fcm_token, title, message_text)
            else:
                logger.info("No FCM token — skipping push")

        else:
            logger.info(f"Skipping unhandled event type: {event_type}")

    return {"statusCode": 200}
