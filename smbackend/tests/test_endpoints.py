from pytest import mark


def test_healthz_endpoint(client):
    response = client.get("/healthz/")
    assert response.status_code == 200


@mark.django_db
def test_readiness_endpoint(client):
    response = client.get("/readiness/")
    assert response.status_code == 200


@mark.django_db
def test_schema_endpoint(client):
    response = client.get("/schema/")
    assert response.status_code == 200


@mark.django_db
def test_swagger_endpoint(client):
    response = client.get("/schema/swagger-ui/")
    assert response.status_code == 200


@mark.django_db
def test_redoc_endpoint(client):
    response = client.get("/schema/redoc/")
    assert response.status_code == 200
