from pytest import mark


def test_healthz_endpoint(client):
    response = client.get("/healthz/")
    assert response.status_code == 200


@mark.django_db
def test_readiness_endpoint(client):
    response = client.get("/readiness/")
    assert response.status_code == 200
