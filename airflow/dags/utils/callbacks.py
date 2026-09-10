# this is used in alerts if an operation fails in am notified by eamil
import logging
import smtplib
from email.mime.text import MIMEText
from airflow.models import Variable

logger = logging.getLogger("airflow.task")


def notify_failure(context: dict) -> None:
    try:
        task_instance = context["task_instance"]
        dag = context.get("dag")
        dag_id = dag.dag_id if dag else "unknown_dag"
        task_id = task_instance.task_id
        execution_date = context.get("logical_date") or context.get("execution_date")
        log_url = getattr(task_instance, "log_url", "N/A")
        exception = context.get("exception", "No exception details provided")
        subject = f"[Airflow Failure] {dag_id}.{task_id}"
        body = (
            f"DAG:{dag_id}\n"
            f"Task:{task_id}\n"
            f"Exception Date:{execution_date}\n"
            f"Exception:{exception}\n"
            f"Log URL:{log_url}\n"
        )

        gmail_user = Variable.get("cross_border_alert_gmail_user")
        gmail_app_password = Variable.get("cross_border_alert_gmail_app_password")
        recipient_str = Variable.get("cross_border_alert_recipient")
        recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = recipient_str

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, recipients, msg.as_string())
        logger.info(f"Failure alert email sent successfully for {dag_id}.{task_id}")

    except Exception as e:
        logger.error(f"Failed to send failure alert email via SMTP:{e}", exc_info=True)