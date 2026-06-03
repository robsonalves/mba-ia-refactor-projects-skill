import logging
import smtplib

from src.config.settings import settings

logger = logging.getLogger(__name__)


def send_email(to, subject, body):
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info("notificacao.email.skipped to=%s subject=%s", to, subject)
        return False
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(settings.SMTP_USER, to, message)
        server.quit()
        logger.info("notificacao.email.sent to=%s", to)
        return True
    except Exception:
        logger.exception("notificacao.email.failed to=%s", to)
        return False


def notify_task_assigned(user, task):
    subject = f"Nova task atribuída: {task.title}"
    body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
    return send_email(user.email, subject, body)


def notify_task_overdue(user, task):
    subject = f"Task atrasada: {task.title}"
    body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
    return send_email(user.email, subject, body)
