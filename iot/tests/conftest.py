import pytest
from rest_framework.test import APIClient

from iot.models import IoTData, IoTDataSource


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def iot_data_source():
    data_source = IoTDataSource.objects.create(
        source_name="S42", source_full_name="Test name", url="www.test.com"
    )
    return data_source


@pytest.mark.django_db
@pytest.fixture
def iot_data(iot_data_source):
    iot_datas = []
    iot_data = IoTData.objects.create(data_source=iot_data_source, data={"test": 42})
    iot_datas.append(iot_data)
    iot_data = IoTData.objects.create(
        data_source=iot_data_source, data={"Even more test": "Data"}
    )
    iot_datas.append(iot_data)
    return iot_datas
