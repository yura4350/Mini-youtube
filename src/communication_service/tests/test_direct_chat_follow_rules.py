from src.dashboard_service.models import Subscription


def _connect_pair(client, user_a: str, user_b: str):
    ws_a = client.websocket_connect(
        f"/comm/direct-chat?user_id={user_a}&username={user_a}&peer_id={user_b}"
    )
    ws_b = client.websocket_connect(
        f"/comm/direct-chat?user_id={user_b}&username={user_b}&peer_id={user_a}"
    )
    # Consume initial history payloads.
    ws_a.receive_json()
    ws_b.receive_json()
    return ws_a, ws_b


def test_non_mutual_follow_allows_only_one_outbound_message_per_sender(client):
    user_a = "rule_a1"
    user_b = "rule_b1"

    ws_a, ws_b = _connect_pair(client, user_a, user_b)
    try:
        ws_a.send_json({"message": "first"})
        first_a = ws_a.receive_json()
        first_b = ws_b.receive_json()
        assert first_a["type"] == "direct_message"
        assert first_b["type"] == "direct_message"

        ws_a.send_json({"message": "second"})
        second_a = ws_a.receive_json()
        assert second_a["type"] == "error"
        assert "only send one message" in second_a["message"]
    finally:
        ws_a.close()
        ws_b.close()


def test_mutual_follow_allows_multiple_messages(client, test_db):
    user_a = "rule_a2"
    user_b = "rule_b2"
    test_db.add_all(
        [
            Subscription(subscriber_user_id=user_a, channel_user_id=user_b),
            Subscription(subscriber_user_id=user_b, channel_user_id=user_a),
        ]
    )
    test_db.commit()

    ws_a, ws_b = _connect_pair(client, user_a, user_b)
    try:
        ws_a.send_json({"message": "first"})
        msg1_a = ws_a.receive_json()
        msg1_b = ws_b.receive_json()
        assert msg1_a["type"] == "direct_message"
        assert msg1_b["type"] == "direct_message"

        ws_a.send_json({"message": "second"})
        msg2_a = ws_a.receive_json()
        msg2_b = ws_b.receive_json()
        assert msg2_a["type"] == "direct_message"
        assert msg2_b["type"] == "direct_message"
    finally:
        ws_a.close()
        ws_b.close()
