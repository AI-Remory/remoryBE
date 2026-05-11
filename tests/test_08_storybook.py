class CapturingStorybookLLMService:
    def __init__(self):
        self.calls = []

    async def generate_storybook(self, title, interview_questions_answers, photo_memory=None):
        self.calls.append(
            {
                "title": title,
                "interview_questions_answers": interview_questions_answers,
                "photo_memory": photo_memory,
            }
        )
        return {
            "summary": f"Generated summary for {title}",
            "chapters": [
                {
                    "title": "Generated Chapter",
                    "summary": "Generated chapter summary",
                    "content": "Generated chapter content",
                }
            ],
        }


def test_create_and_get_storybook(client, auth_headers, created_storybook):
    response = client.get(f"/api/v1/storybooks/{created_storybook['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_storybook["id"]
    assert response.json()["status"] == "GENERATED"
    assert len(response.json()["chapters"]) >= 1


def test_list_storybooks(client, auth_headers, created_storybook):
    response = client.get("/api/v1/storybooks", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_storybook_chapters(client, auth_headers, created_storybook):
    response = client.get(f"/api/v1/storybooks/{created_storybook['id']}/chapters", headers=auth_headers)
    assert response.status_code == 200
    assert [chapter["order_index"] for chapter in response.json()] == [1]


def test_create_storybook_passes_source_context_to_llm(client, auth_headers, created_interview, monkeypatch):
    llm_service = CapturingStorybookLLMService()
    monkeypatch.setattr("app.services.storybook_service.get_llm_service", lambda: llm_service)

    response = client.post(
        "/api/v1/storybooks",
        json={"title": "Captured Story", "interview_session_id": created_interview["session"]["id"]},
        headers=auth_headers,
    )

    assert response.status_code == 201
    call = llm_service.calls[-1]
    assert call["title"] == "Captured Story"
    assert call["interview_questions_answers"] == [
        {
            "question_text": created_interview["question"]["question_text"],
            "answers": [created_interview["answer"]["answer_text"]],
        }
    ]
    assert call["photo_memory"] == {}
    assert len(response.json()["chapters"]) == 1


def test_regenerate_storybook(client, auth_headers, created_storybook):
    response = client.post(f"/api/v1/storybooks/{created_storybook['id']}/regenerate", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_storybook["id"]


def test_regenerate_storybook_uses_llm_generation(client, auth_headers, created_storybook, monkeypatch):
    llm_service = CapturingStorybookLLMService()
    monkeypatch.setattr("app.services.storybook_service.get_llm_service", lambda: llm_service)

    response = client.post(f"/api/v1/storybooks/{created_storybook['id']}/regenerate", headers=auth_headers)

    assert response.status_code == 200
    assert llm_service.calls[-1]["title"] == created_storybook["title"]
    assert llm_service.calls[-1]["interview_questions_answers"]
    assert response.json()["summary"] == f"Generated summary for {created_storybook['title']}"


def test_other_user_cannot_access_storybook(client, created_storybook, second_user_headers):
    response = client.get(f"/api/v1/storybooks/{created_storybook['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)
