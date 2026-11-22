"""Provider e-mail after the merge (mcod/aed/notifications.py). Needs the portal test stack (Postgres)."""
from pathlib import Path
from unittest.mock import patch

from django.core import mail

from mcod.aed.aed_utils import build_main_aed_list, get_all_aed_list_resources
from mcod.aed.aed_utils import update_or_create_aggr_aed_info_and_delete_old_main_aed as save_merge
from mcod.aed.models import AggregatedAEDInfo
from mcod.datasets.factories import DatasetFactory
from mcod.resources.factories import ResourceFactory

KROSNO = (Path(__file__).parent / "data" / "krosno_resource_54632.csv").read_bytes()  # real file, rejected
GOOD_LIST = (
    "nazwa,miejscowosc,szerokosc_geograficzna,dlugosc_geograficzna,dostep\n"
    "Urząd Miasta Legionowo,Legionowo,52.395198,20.931382,publiczny\n"
).encode("utf-8")


def _merge(resource, data):
    """One merge run on the given file content of the provider's list -> report saved in AggregatedAEDInfo."""
    with patch("mcod.aed.aed_utils.read_resource_bytes", return_value=(data, None)):
        _, report = build_main_aed_list(get_all_aed_list_resources())
    save_merge(ResourceFactory.create(status="published"), report)
    return report


def _provider_list():
    dataset = DatasetFactory.create(update_notification_recipient_email="aed@krosno.example.gov.pl")
    return ResourceFactory.create(dataset=dataset, contains_aed_list=True, status="published")


def test_rejected_list_mailed_once_then_accepted_message():
    resource = _provider_list()

    _merge(resource, KROSNO)
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["aed@krosno.example.gov.pl"]
    assert message.subject.startswith("Wykaz AED odrzucony")
    assert "Kolumna spoza standardu AED." in message.body  # fixed description, not the file's raw text
    assert "„Adres”" not in message.body
    assert "/resources/resource/%s/change/" % resource.pk in message.body
    assert message.alternatives[0][1] == "text/html"

    _merge(resource, KROSNO)  # the same result next day: no repeat
    assert len(mail.outbox) == 1

    _merge(resource, GOOD_LIST)  # fixed
    assert len(mail.outbox) == 2
    assert mail.outbox[1].subject.startswith("Wykaz AED przyjęty w całości")

    _merge(resource, GOOD_LIST)  # still fine: nothing
    assert len(mail.outbox) == 2


def test_smtp_error_does_not_stop_the_merge():
    resource = _provider_list()
    with patch("django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("SMTP down")):
        _merge(resource, KROSNO)
    info = AggregatedAEDInfo.objects.get()
    assert info.resource is not None
    assert info.report["wykazy"][0]["status"] == "odrzucony"
    assert len(mail.outbox) == 0

    _merge(resource, KROSNO)  # SMTP is back: the same result is still owed to the provider
    assert len(mail.outbox) == 1
    _merge(resource, KROSNO)  # delivered: no repeat
    assert len(mail.outbox) == 1


def test_switch_off():
    resource = _provider_list()
    with patch("mcod.aed.constants.NOTIFY_PROVIDERS", False):
        _merge(resource, KROSNO)
    assert mail.outbox == []


def test_zero_sent_is_retried_next_merge():
    resource = _provider_list()
    with patch("django.core.mail.EmailMultiAlternatives.send", return_value=0):
        report = _merge(resource, KROSNO)
    assert report["wykazy"][0].get("powiadomienie_oczekuje") is True
    _merge(resource, KROSNO)  # same result, but the message is still owed
    assert len(mail.outbox) == 1


def test_mail_backend_error_marks_all_entries():
    resource = _provider_list()
    with patch("mcod.aed.notifications.get_connection", side_effect=RuntimeError("no backend")):
        report = _merge(resource, KROSNO)
    assert all(w.get("powiadomienie_oczekuje") for w in report["wykazy"])


def test_warnings_alone_never_send_mail():
    """Warnings (e.g. a 6-digit TERC, standard 0.3.0) do not lower the list's status and do not send or repeat the
    mail: a list accepted with warnings gets none, and a partly accepted list is not mailed again when only its
    warnings change."""
    header = "nazwa,miejscowosc,kod_terc,szerokosc_geograficzna,dlugosc_geograficzna,dostep\n"
    good, warned = "Urząd,Legionowo,1408011,52.395198,20.931382,publiczny\n", "Urząd,Legionowo,140801,52.395198,20.931382,publiczny\n"
    outside = "Szkoła,Legionowo,,10.0,10.0,publiczny\n"  # coordinates outside Poland: the row is rejected

    first = _provider_list()
    accepted = _merge(first, (header + warned).encode("utf-8"))
    assert accepted["wykazy"][0]["status"] == "przyjety" and accepted["wykazy"][0]["problemy"][0]["kod"] == "terc_bez_rodzaju"
    assert len(mail.outbox) == 0

    first.contains_aed_list = False  # out of the next merges
    first.save()
    resource = _provider_list()
    _merge(resource, (header + good + outside).encode("utf-8"))
    assert len(mail.outbox) == 1 and mail.outbox[0].subject.startswith("Wykaz AED przyjęty częściowo")
    _merge(resource, (header + warned + outside).encode("utf-8"))  # same errors, one warning more
    assert len(mail.outbox) == 1
