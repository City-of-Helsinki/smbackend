from unittest.mock import MagicMock, call, patch

import pytest
from django.contrib.gis.gdal.error import GDALException

from services.management.commands.lipas_import import fetch_layer


@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.DataSource")
def test_fetch_layer_succeeds_on_first_attempt(mock_datasource, mock_sleep):
    mock_layer = MagicMock()
    mock_datasource.return_value.__getitem__.return_value = mock_layer

    result = fetch_layer("WFS:http://example.com", retries=3, backoff=1)

    assert result is mock_layer
    mock_datasource.assert_called_once_with("WFS:http://example.com")
    mock_sleep.assert_not_called()


@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.DataSource")
def test_fetch_layer_retries_on_gdal_exception(mock_datasource, mock_sleep):
    mock_layer = MagicMock()
    mock_datasource.return_value.__getitem__.side_effect = [
        GDALException("502 Bad Gateway"),
        GDALException("502 Bad Gateway"),
        mock_layer,
    ]

    result = fetch_layer("WFS:http://example.com", retries=3, backoff=2)

    assert result is mock_layer
    assert mock_datasource.call_count == 3
    assert mock_sleep.call_args_list == [call(2), call(4)]


@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.DataSource")
def test_fetch_layer_raises_after_all_retries_exhausted(mock_datasource, mock_sleep):
    mock_datasource.return_value.__getitem__.side_effect = GDALException(
        "502 Bad Gateway"
    )

    with pytest.raises(GDALException):
        fetch_layer("WFS:http://example.com", retries=3, backoff=1)

    assert mock_datasource.call_count == 3
    assert mock_sleep.call_count == 2


@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.DataSource")
def test_fetch_layer_no_sleep_on_single_attempt(mock_datasource, mock_sleep):
    mock_datasource.return_value.__getitem__.side_effect = GDALException("error")

    with pytest.raises(GDALException):
        fetch_layer("WFS:http://example.com", retries=1, backoff=5)

    mock_sleep.assert_not_called()


@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.DataSource")
def test_fetch_layer_exponential_backoff_timing(mock_datasource, mock_sleep):
    mock_datasource.return_value.__getitem__.side_effect = GDALException("error")

    with pytest.raises(GDALException):
        fetch_layer("WFS:http://example.com", retries=4, backoff=10)

    assert mock_sleep.call_args_list == [call(10), call(20), call(30)]


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.fetch_layer")
def test_command_skips_layer_on_fetch_failure(mock_fetch_layer, mock_sleep):
    from datetime import datetime

    import pytz
    from django.core.management import call_command

    from services.models import Unit, UnitIdentifier

    mock_fetch_layer.side_effect = GDALException("server unavailable")

    unit = Unit.objects.create(
        id=1, last_modified_time=datetime.now(pytz.utc), name_fi="Test Unit"
    )
    UnitIdentifier.objects.create(unit_id=unit.id, namespace="lipas", value="12345")

    call_command("lipas_import")

    unit.refresh_from_db()
    assert unit.geometry is None


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.time.sleep")
@patch("services.management.commands.lipas_import.fetch_layer")
def test_command_skips_failed_layer_but_processes_successful_one(
    mock_fetch_layer, mock_sleep
):
    from datetime import datetime

    import pytz
    from django.core.management import call_command

    from services.models import Unit, UnitIdentifier

    successful_layer = MagicMock()
    successful_layer.__iter__ = MagicMock(return_value=iter([]))
    successful_layer.__len__ = MagicMock(return_value=0)

    mock_fetch_layer.side_effect = [
        GDALException("paths unavailable"),
        successful_layer,
    ]

    unit = Unit.objects.create(
        id=1, last_modified_time=datetime.now(pytz.utc), name_fi="Test Unit"
    )
    UnitIdentifier.objects.create(unit_id=unit.id, namespace="lipas", value="12345")

    call_command("lipas_import")

    assert mock_fetch_layer.call_count == 2
