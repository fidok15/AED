"""XML harvester schema 1.14: containsAedList marks a harvested resource as an AED list. Modelled on
mcod/harvester/tests/test_serializers.py (the same 1.13 sample, moved to 1.14)."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mcod.harvester.serializers import XMLResourceSchema
from mcod.harvester.utils import get_xml_as_dict
from mcod.lib.utils import get_file_content

PROTECTED = "<containsProtectedData>false</containsProtectedData>"  # keeps the DGA checks out of this test
SAMPLE_1_13 = (
    get_file_content(Path("harvester") / "import_example1.13.xml")
    .decode("utf-8")
    .replace("<containsProtectedData>true</containsProtectedData>", PROTECTED)
)


def _first_resource(xml: str, version: str) -> dict:
    raw = get_xml_as_dict(source=xml.encode("utf-8"), version=version)["dataset"][0]["resources"]["resource"][0]
    for key in ("supplements", "regions"):  # fetched from the network on load; not needed here
        raw.pop(key, None)
    with patch("mcod.harvester.serializers.get_and_validate_resource_format_from_response"):
        return XMLResourceSchema(context={"organization": SimpleNamespace(pk=0, institution_type="local")}).load(raw)


def test_contains_aed_list_in_schema_1_14():
    xml = SAMPLE_1_13.replace("harvester:1.13", "harvester:1.14")
    xml = xml.replace(PROTECTED, PROTECTED + "<containsAedList>true</containsAedList>", 1)
    assert _first_resource(xml, "1.14")["contains_aed_list"] is True


def test_schema_1_13_and_1_14_without_the_element_leave_the_flag_alone():
    assert "contains_aed_list" not in _first_resource(SAMPLE_1_13, "1.13")
    assert "contains_aed_list" not in _first_resource(SAMPLE_1_13.replace("harvester:1.13", "harvester:1.14"), "1.14")
