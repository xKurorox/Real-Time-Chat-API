from app.main import app
from app.models import Message
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
import pytest

test_engine = create_engine("sqlite:///./test.db", connect_args = {"check_same_thread": False})
TestSession = sessionmaker(bind = test_engine)

@pytest.fixture(autouse = True)
def clean_database():
    Base.metadata.drop_all(bind = test_engine)
    Base.metadata.create_all(bind = test_engine)
    yield

Base.metadata.create_all(bind = test_engine)

def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_user_no_email():
    response = client.post("/users", json= {"name": "testuser"})
    assert response.status_code == 200
    assert response.json()["name"] == "testuser"
    assert response.json()["id"] is not None

def test_create_user():
    response = client.post("/users", json= {"name": "testuser", "email": "testemail"})
    assert response.status_code == 200
    assert response.json()["name"] == "testuser"
    assert response.json()["email"] == "testemail"

def test_no_username():
    response = client.post("/users", json= {})
    assert response.status_code == 422

def test_duplicate_user():
    response = client.post("/users", json= {"name": "testuser"})
    response2 = client.post("/users", json= {"name": "testuser"})
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Username already taken"

def test_create_room():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    response = client.post("/rooms", json={"name": "test_room", "user_id": user_id})
    assert response.status_code == 200
    assert response.json()["name"] == "test_room"

def test_duplicate_room():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    response = client.post("/rooms", json= {"name": "test_room", "user_id": user_id})
    response2 = client.post("/rooms", json= {"name": "test_room", "user_id": user_id})
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Room name already taken"

def test_room_incorrect_user_id():
    response = client.post("/rooms", json= {"name": "test_room", "user_id": 1})
    assert response.status_code == 404
    assert response.json()["detail"] == "Not a valid user id"

def test_join_room():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    user_response2 = client.post("/users", json= {"name": "testuser2"})
    user_id_2 = user_response2.json()["id"]
    room = client.post("/rooms", json= {"name": "test_room", "user_id": user_id})
    room_id = room.json()["id"]
    response = client.post(f"/rooms/{room_id}/members", json= {"user_id": user_id_2})
    assert response.status_code == 200


def test_duplicate_user_joined_room():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    room = client.post("/rooms", json= {"name": "test_room", "user_id": user_id})
    room_id = room.json()["id"]
    response = client.post(f"/rooms/{room_id}/members", json= {"user_id": user_id})
    assert response.status_code == 409
    assert response.json()["detail"] == "User is already in room"

def test_room_does_not_exist():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    response = client.post("/rooms/1/members", json= {"user_id": user_id})
    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"

def test_join_room_user_does_not_exist():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    room = client.post("/rooms", json= {"name": "test_room", "user_id": user_id})
    room_id = room.json()["id"]
    response = client.post(f"/rooms/{room_id}/members", json= {"user_id": 4})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_get_messages():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    room_response = client.post("/rooms", json={"name": "testroom", "user_id": user_id})
    room_id = room_response.json()["id"]
    
    db = TestSession()
    for i in range(5):
        message = Message(text=f"message {i}", user_id=user_id, room_id=room_id)
        db.add(message)
    db.commit()
    db.close()
    
    response = client.get(f"/rooms/{room_id}/messages")
    assert response.status_code == 200
    assert len(response.json()) == 5

def test_message_pagination():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    room_response = client.post("/rooms", json={"name": "testroom", "user_id": user_id})
    room_id = room_response.json()["id"]
    
    db = TestSession()
    for i in range(25):
        message = Message(text=f"message {i}", user_id=user_id, room_id=room_id)
        db.add(message)
    db.commit()
    db.close()
    
    first_page = client.get(f"/rooms/{room_id}/messages?limit=20")
    assert len(first_page.json()) == 20
    
    oldest_id = first_page.json()[-1]["id"]
    second_page = client.get(f"/rooms/{room_id}/messages?limit=20&before={oldest_id}")
    assert len(second_page.json()) == 5

def test_get_messages_invalid_room():
    response = client.get("/rooms/9999/messages")
    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"

def test_websocket_join():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "join", "user_id": user_id})
        response = websocket.receive_json()
        assert response["type"] == "presence"
        assert response["username"] == "testuser"
        assert response["status"] == "online"

def test_websocket_message():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    room = client.post("/rooms", json={"name": "test_room", "user_id": user_id})
    room_id = room.json()["id"]

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "join", "user_id": user_id})
        join_response = websocket.receive_json()
        assert join_response["type"] == "presence"
        assert join_response["status"] == "online"
        websocket.send_json({"type": "message", "user_id": user_id, "room_id": room_id, "text": "i am the best"})
        response = websocket.receive_json()
        assert response["id"] is not None
        assert response["user_id"] == user_id
        assert response["text"] == "i am the best"
        assert response["room_id"] == room_id
        assert response["username"] == "testuser"
        assert response["created_at"] is not None

def test_websocket_typing():
    user_response = client.post("/users", json={"name": "testuser"})
    user_id = user_response.json()["id"]
    user_response2 = client.post("/users", json={"name": "testuser2"})
    user_id2 = user_response2.json()["id"]
    room = client.post("/rooms", json={"name": "test_room", "user_id": user_id})
    room_id = room.json()["id"]
    client.post(f"/rooms/{room_id}/members", json= {"user_id": user_id2})

    with client.websocket_connect("/ws") as websocket1:
        with client.websocket_connect("/ws") as websocket2:
            websocket1.send_json({"type": "join", "user_id": user_id})
            join_response = websocket1.receive_json()
            websocket2.receive_json()
            assert join_response["type"] == "presence"
            assert join_response["status"] == "online"
            websocket2.send_json({"type": "join", "user_id": user_id2})
            join_response2 = websocket2.receive_json()
            websocket1.receive_json()
            assert join_response2["type"] == "presence"
            assert join_response2["status"] == "online"
            websocket1.send_json({"type": "typing", "user_id": user_id, "room_id": room_id})
            response = websocket2.receive_json()
            assert response["type"] == "typing"
            assert response["username"] == "testuser"
            assert response["room_id"] == room_id