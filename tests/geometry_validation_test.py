import pytest
from unittest.mock import MagicMock, patch

from geoalchemy2 import Geometry
from sqlalchemy import Column

from SAGisXPlanung.core.geometry_validation import (
    _strip_gml_prefix,
    _points_to_wkt,
    _collect_xids,
    _parse_geometric_message,
    validate_geometric_xplan_validator,
    XPlanValidationError,
    GeometryViolationType,
)

class DummyType:
    __geometry_column_name__ = "geom"
    geom = Column(Geometry)


@pytest.fixture
def type_lookup():
    return {
        "68bd413b-2669-4eed-9fff-5fcd31deb17b": DummyType,
        "b8337201-f1a3-4e74-99cc-244703fb3bd7": DummyType,
        "c9de1a6e-70dd-4f60-ab71-8f3900c94aa7": DummyType,
        "65113694-d73b-4b0e-8079-28e9feb80b26": DummyType,
        "33724661-b198-4913-a813-08fbb24d4577": DummyType,
        "e98e585c-2c73-48f2-b368-2b7c9cfe7b76": DummyType,
    }


def test_strip_gml_prefix():
    assert (
        _strip_gml_prefix("GML_abc")
        == "abc"
    )


def test_strip_gml_prefix_none():
    assert _strip_gml_prefix(None) is None


def test_strip_gml_prefix_without_prefix():
    assert (
        _strip_gml_prefix("abc")
        == "abc"
    )

def test_points_to_wkt_single():
    msg = (
        "foo (351245.320865982,5636886.68840365)"
    )

    assert (
        _points_to_wkt(msg)
        == "POINT(351245.320865982 5636886.68840365)"
    )


def test_points_to_wkt_multi():
    msg = (
        "foo "
        "(351222.11346964946,5636899.141576428),"
        "(351359.84098039294,5636720.306203763)"
    )

    assert (
        _points_to_wkt(msg)
        ==
        "MULTIPOINT("
        "(351222.11346964946 5636899.141576428),"
        "(351359.84098039294 5636720.306203763)"
        ")"
    )


def test_points_to_wkt_none():
    assert _points_to_wkt("no coordinates") is None


def test_collect_xids():
    messages = [
        "foo GML_abc",
        "bar GML_def",
        "baz GML_abc",
    ]

    assert _collect_xids(messages) == {
        "abc",
        "def",
    }


@patch("SAGisXPlanung.core.geometry_validation.Session")
@patch("SAGisXPlanung.core.geometry_validation.select")
@patch("SAGisXPlanung.core.geometry_validation.func")
def test_parse_fully_within(
    mock_func,
    mock_select,
    mock_session,
    type_lookup,
):
    mock_stmt = MagicMock()
    mock_select.return_value.filter_by.return_value = mock_stmt

    session_ctx = MagicMock()
    session_ctx.execute.return_value.scalar_one.return_value = (
        "POLYGON((0 0,1 0,1 1,0 1,0 0))"
    )

    mock_session.return_value.__enter__.return_value = session_ctx

    msg = (
        "2.2.1.1: Das Flächenschlussobjekt "
        "mit der gml id "
        "GML_68bd413b-2669-4eed-9fff-5fcd31deb17b "
        "überdeckt das Flächenschlussobjekt "
        "mit der gml id "
        "GML_b8337201-f1a3-4e74-99cc-244703fb3bd7 "
        "vollständig."
    )

    result = _parse_geometric_message(
        msg,
        type_lookup,
    )

    assert result.xid == (
        "68bd413b-2669-4eed-9fff-5fcd31deb17b"
    )

    assert result.other_xid == (
        "b8337201-f1a3-4e74-99cc-244703fb3bd7"
    )

    assert (
        result.intersection_type
        == GeometryViolationType.FullyWithin
    )

    assert result.geom_wkt.startswith("POLYGON")


def test_parse_not_in_plan(type_lookup):
    msg = (
        "2.2.3.1: Das Objekt mit der gml id "
        "GML_c9de1a6e-70dd-4f60-ab71-8f3900c94aa7 "
        "liegt nicht vollständig im Geltungsbereich "
        "des Plans mit der gml id "
        "GML_65113694-d73b-4b0e-8079-28e9feb80b26 "
        "und des Bereichs "
        "mit der gml id "
        "GML_65113694-d73b-4b0e-8079-28e9feb80b26. "
        "Schnittpunkte mit dem Umring des "
        "Geltungsbereichs: "
        "(351222.11346964946,5636899.141576428),"
        "(351359.84098039294,5636720.306203763)"
    )

    result = _parse_geometric_message(
        msg,
        type_lookup,
    )

    assert (
        result.intersection_type
        == GeometryViolationType.Bereich
    )

    assert result.geom_wkt == (
        "MULTIPOINT("
        "(351222.11346964946 5636899.141576428),"
        "(351359.84098039294 5636720.306203763)"
        ")"
    )


def test_parse_gap_warning(type_lookup):
    msg = (
        "2.2.1.1: Das Flächenschlussobjekt "
        "mit der gml id "
        "GML_33724661-b198-4913-a813-08fbb24d4577 "
        "erfüllt die Flächenschlussbedingung "
        "an folgender Stelle nicht, "
        "es könnte sich um eine Lücke handeln: "
        "(351330.074139918,5636777.21804174)"
    )

    result = _parse_geometric_message(
        msg,
        type_lookup,
    )

    assert (
        result.intersection_type
        == GeometryViolationType.NotCovered
    )

    assert result.geom_wkt == (
        "POINT(351330.074139918 5636777.21804174)"
    )


#
# ------------------------------------------------------------------
# validate_geometric_xplan_validator
# ------------------------------------------------------------------
#

@patch("SAGisXPlanung.core.geometry_validation.export_plan")
@patch("SAGisXPlanung.core.geometry_validation.requests.post")
@patch("SAGisXPlanung.core.geometry_validation._build_type_lookup")
def test_validate_geometric_validator_success(
    mock_build_lookup,
    mock_post,
    mock_export,
):
    mock_export.return_value = b"<xml />"

    mock_build_lookup.return_value = {}

    response = MagicMock()

    response.json.return_value = {
        "validationResult": {
            "syntaktisch": {
                "valid": True,
                "messages": [],
            },
            "geometrisch": {
                "errors": [],
                "warnings": [],
            },
        }
    }

    mock_post.return_value = response

    results = validate_geometric_xplan_validator(
        plan_id="foo",
        set_status=lambda _: None,
    )

    assert results == []


@patch("SAGisXPlanung.core.geometry_validation.export_plan")
@patch("SAGisXPlanung.core.geometry_validation.requests.post")
def test_validate_geometric_validator_syntactic_error(
    mock_post,
    mock_export,
):
    mock_export.return_value = b"<xml />"

    response = MagicMock()

    response.json.return_value = {
        "validationResult": {
            "syntaktisch": {
                "valid": False,
                "messages": [
                    "XML kaputt"
                ],
            }
        }
    }

    mock_post.return_value = response

    with pytest.raises(XPlanValidationError):
        validate_geometric_xplan_validator(
            plan_id="foo",
            set_status=lambda _: None,
        )