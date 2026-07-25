from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


@patch("backend.main.get_answer")
@patch("backend.main.retrieve_chunks")
@patch("backend.main.check_rate_limit", return_value=True)
def test_ask_returns_answer(mock_rate, mock_retrieve, mock_answer):
    mock_retrieve.return_value = [
        {"module": 1, "start_time": 0, "end_time": 10, "text": "Introduction excerpt."}
    ]
    mock_answer.return_value = "See [Module 1 at 00:00] for details."

    resp = client.post(
        "/ask",
        json={"question": "What is covered first?", "current_module": 1, "history": []},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "See [Module 1 at 00:00] for details."
    mock_retrieve.assert_called_once()
    mock_answer.assert_called_once()


@patch("backend.main.check_rate_limit", return_value=False)
def test_ask_rate_limited(mock_rate):
    resp = client.post("/ask", json={"question": "test", "history": []})
    assert resp.status_code == 429


def test_ask_empty_question():
    resp = client.post("/ask", json={"question": "   ", "history": []})
    assert resp.status_code == 400


@patch("backend.main.retrieve_chunks", side_effect=RuntimeError("pinecone down"))
@patch("backend.main.check_rate_limit", return_value=True)
def test_ask_retrieval_error_is_generic(mock_rate, mock_retrieve):
    resp = client.post("/ask", json={"question": "hello", "history": []})
    assert resp.status_code == 500
    assert resp.json()["detail"] == "Database retrieval failed."
