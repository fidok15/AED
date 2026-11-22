"""E-mail to the provider whose AED list was rejected (or accepted only in part) by the merge, as the portal's
dataset update reminder (Dataset.send_dataset_update_reminder_mails). Only when the result for that resource
changed since the previous merge, plus one message when a previously rejected list passes."""
import logging
from typing import Any, Dict, List, Optional

from constance import config
from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils import translation

from aed_standard.validate import ERROR
from mcod.aed import constants as C

logger = logging.getLogger("mcod")

PROBLEM_STATUSES = ("odrzucony", "czesciowo")


PENDING_KEY = "powiadomienie_oczekuje"  # set on a report entry whose message failed; the next merge retries it


def _signature(entry: Dict[str, Any]):
    problems = tuple((p["wiersz"], p["pole"], p["kod"], p["komunikat"]) for p in entry.get("problemy", []))
    return entry["status"], entry.get("wiersze", 0) - entry.get("przyjete", 0), entry.get("problemy_razem", 0), problems


def lists_to_notify(old_report: Optional[Dict[str, Any]], new_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Entries of new_report worth a message: a problem result that differs from the previous merge, or a list
    that passes after a problem result."""
    old = {w["zasob"]: w for w in (old_report or {}).get("wykazy", [])}
    result = []
    for entry in new_report.get("wykazy", []):
        previous = old.get(entry["zasob"])
        pending = previous is not None and previous.get(PENDING_KEY)  # the last message was not delivered
        if entry["status"] in PROBLEM_STATUSES:
            if previous is None or pending or _signature(previous) != _signature(entry):
                result.append(entry)
        elif previous is not None and (pending or previous["status"] in PROBLEM_STATUSES):
            result.append(entry)
    return result


def recipient(dataset) -> Optional[str]:
    """Institutional contact only: the dataset's notification address, else the institution's e-mail. Unlike the
    portal's reminder there is no fallback to the editor's personal address (dataset.modified_by)."""
    return dataset.update_notification_recipient_email or dataset.organization.email or None


def build_message(entry: Dict[str, Any], resource) -> Optional[EmailMultiAlternatives]:
    to = recipient(resource.dataset)
    if not to:
        logger.warning("AED list %s: no institutional e-mail, provider not notified.", resource.pk)
        return None
    problems = sorted(entry.get("problemy", []), key=lambda p: p["poziom"] != ERROR)[: C.FORM_MAX_MESSAGES]
    context = {
        "entry": entry,
        "rejected_rows": entry.get("wiersze", 0) - entry.get("przyjete", 0),
        "problems": problems,
        "more_problems": max(entry.get("problemy_razem", 0) - len(problems), 0),
        "resource_title": resource.title,
        "dataset_title": resource.dataset.title,
        "admin_url": "%s/resources/resource/%s/change/" % (settings.ADMIN_URL, resource.pk),
        "dataset_url": resource.dataset.frontend_absolute_url,
        "report_url": "%s/aed-aggregated" % settings.API_URL,
        "help_url": C.LIST_HELP_URL,
        "host": settings.BASE_URL,
    }
    subject = {
        "odrzucony": "Wykaz AED odrzucony: %s",
        "czesciowo": "Wykaz AED przyjęty częściowo: %s",
    }.get(entry["status"], "Wykaz AED przyjęty w całości: %s") % resource.title
    with translation.override("pl"):
        body = render_to_string("mails/aed-list-result.txt", context)
        html = render_to_string("mails/aed-list-result.html", context)
    message = EmailMultiAlternatives(subject.replace("\n", " ").replace("\r", ""), body, config.NO_REPLY_EMAIL, [to])
    message.attach_alternative(html, "text/html")
    return message


def notify_aed_list_providers(old_report: Optional[Dict[str, Any]], new_report: Dict[str, Any]) -> int:
    """Sends the messages; never raises, so a mail problem does not undo the merge. -> number sent.

    An entry whose message failed gets PENDING_KEY in new_report (the caller saves it), so the next merge
    sends it even when the result is unchanged."""
    if not C.NOTIFY_PROVIDERS:
        return 0
    sent = 0
    try:
        entries = lists_to_notify(old_report, new_report)
        resources = apps.get_model("resources", "Resource").raw.select_related("dataset__organization")
        connection = get_connection(settings.EMAIL_BACKEND)
    except Exception as exc:
        logger.error("AED list notifications skipped: %s", exc)
        return 0
    for entry in entries:
        try:
            message = build_message(entry, resources.get(pk=entry["zasob"]))
            if message:
                message.connection = connection
                sent += message.send()
        except Exception as exc:
            entry[PENDING_KEY] = True
            logger.error("AED list %s: provider notification failed: %s", entry.get("zasob"), exc)
    logger.info("AED list notifications sent: %s of %s.", sent, len(entries))
    return sent
