import pytest

from mobility_data.importers.bike_service_stations import CONTENT_TYPE_NAME
from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_import_bike_service_stations():
    import_command(
        "import_bike_service_stations", test_mode="bike_service_stations.geojson"
    )
    assert ContentType.objects.filter(name=CONTENT_TYPE_NAME).count() == 1
    assert MobileUnit.objects.filter(content_types__name=CONTENT_TYPE_NAME).count() == 3
    kupittaankentta = MobileUnit.objects.get(name="Kupittaankenttä")
    assert kupittaankentta.name_sv == "Kuppisplan"
    assert kupittaankentta.name_en == "Kupittaa court"
    assert kupittaankentta.address == "Uudenmaankatu 18"
    assert kupittaankentta.address_sv == "Nylandsgatan 18"
    assert kupittaankentta.address_en == "Uudenmaankatu 18"
    assert "pyöränpumpun ja kaksi monitoimityökalua" in kupittaankentta.description
    assert "cykelpump och två multiverktyg" in kupittaankentta.description_sv
    assert (
        "includes bicycle pump and two multifunctional tools"
        in kupittaankentta.description_en
    )
    assert kupittaankentta.extra["in_terrain"] == "Ei"
    assert kupittaankentta.extra["additional_details"] == "Merkki Care4bikes"
    roola = MobileUnit.objects.get(name="Röölä")
    assert roola.name_sv == "Röölä"
    assert roola.name_en == "Röölä"
    assert roola.extra["in_terrain"] == "Kyllä"
