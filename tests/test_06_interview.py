def test_create_interview_question_answer_and_detail(client, auth_headers, created_interview):
    session_id = created_interview["session"]["id"]
    response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == session_id
    assert len(payload["questions"]) == 1
    assert len(payload["questions"][0]["answers"]) == 1


def test_target_profile_interview_requires_target(client, auth_headers):
    response = client.post(
        "/api/v1/interviews",
        json={"session_type": "TARGET_PROFILE"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_other_user_cannot_access_interview(client, created_interview, second_user_headers):
    response = client.get(
        f"/api/v1/interviews/{created_interview['session']['id']}",
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
