from typing import Any
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def send_email_ses(
    send_from: str,
    email_list: list,
    subject: str,
    body: str,
    credentials: dict[str, Any],
    html: bool = False,
):
    ses = boto3.client("ses", **credentials)
    charset = "UTF-8"
    body_type = "Html" if html else "Text"

    try:
        for recipient_email in email_list:
            response = ses.send_email(
                Source=send_from,
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": charset},
                    "Body": {body_type: {"Data": body, "Charset": charset}},
                },
            )
            print(
                f"Email sent to {recipient_email}: Message ID - {response['MessageId']}"
            )
    except NoCredentialsError:
        print("AWS credentials not found.")
    except PartialCredentialsError:
        print("Incomplete AWS credentials.")
    except Exception as e:
        print(f"Error: {e}")
