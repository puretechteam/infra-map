from app import app


def test_app_creation():
    assert app is not None
    assert app.name == "app"


def test_root_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_root_route_content_type(client):
    response = client.get("/")
    assert "text/html" in response.content_type
