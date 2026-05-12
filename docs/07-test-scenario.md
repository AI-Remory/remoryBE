# 07. Test Scenario

## 목차

- [Pytest 실행](#pytest-실행)
- [테스트 환경](#테스트-환경)
- [API 테스트 순서](#api-테스트-순서)
- [데모 시나리오](#데모-시나리오)
- [GitHub Actions](#github-actions)
- [수동 점검](#수동-점검)

## Pytest 실행

전체 테스트:

```powershell
cd D:\IdeaProjects\remory\backend
.\.venv\Scripts\activate
pytest -v
```

일부 테스트:

```powershell
pytest tests/test_01_auth.py -v
pytest tests/test_05_chat.py -v
pytest tests/test_19_realtime_voice.py -v
```

마이그레이션 확인:

```powershell
alembic upgrade head
```

## 테스트 환경

- Test runner: `pytest`
- Client: FastAPI `TestClient`
- DB: in-memory SQLite
- AI: `MockLLMService`
- STT: `MockSTTService`
- TTS: `MockTTSService`
- VoiceClone: `MockVoiceCloneService`
- Upload cleanup: 테스트 전후 `uploads/` 하위 테스트 산출물 정리

테스트에서는 Gemini, faster-whisper, MeloTTS, OpenVoice가 직접 호출되면 안 된다.

## API 테스트 순서

권장 end-to-end 순서:

1. `GET /health`
2. `POST /api/v1/auth/register`
3. `POST /api/v1/auth/login`
4. `GET /api/v1/auth/me`
5. `POST /api/v1/targets`
6. `POST /api/v1/consents`
7. `POST /api/v1/targets/{target_id}/verification-requests`
8. Admin `PATCH /api/v1/admin/verification-requests/{request_id}/approve`
9. `POST /api/v1/targets/{target_id}/media`
10. `POST /api/v1/targets/{target_id}/persona`
11. `POST /api/v1/personas/{persona_id}/voice-profile`
12. `POST /api/v1/personas/{persona_id}/voice-profile/evaluate`
13. `PATCH /api/v1/personas/{persona_id}/voice-profile/user-confirm`
14. `POST /api/v1/personas/{persona_id}/chats`
15. `POST /api/v1/chats/{chat_id}/messages`
16. `POST /api/v1/chats/{chat_id}/audio`
17. `WS /api/v1/ws/personas/{persona_id}/voice`
18. `POST /api/v1/interviews`
19. `POST /api/v1/interviews/{session_id}/questions`
20. `POST /api/v1/interviews/{session_id}/answers`
21. `POST /api/v1/photo-memories`
22. `POST /api/v1/storybooks`
23. `POST /api/v1/storybooks/{storybook_id}/share-links`
24. `GET /api/v1/share/{token}`
25. `POST /api/v1/groups`
26. `POST /api/v1/groups/{group_id}/members`
27. `POST /api/v1/groups/{group_id}/storybooks/{storybook_id}`
28. `POST /api/v1/deletion-requests`
29. Admin report/audit/usage/rate-limit checks

## 데모 시나리오

### Persona 생성 데모

1. 사용자 회원가입/로그인
2. "Mom" target 생성
3. 필수 consent 생성
4. verification 문서 제출
5. admin 승인
6. 사진과 음성 media 업로드
7. persona 생성
8. persona 상세와 status 확인

### Chat/Voice 데모

1. persona chat 생성
2. 텍스트 메시지 전송
3. persona reply와 `is_ai_generated=true` 확인
4. 음성 파일 업로드
5. STT 결과가 USER `PersonaMessage.content`로 저장되는지 확인
6. voice profile READY/user-confirm 후 `generate_audio=true`로 audio path 확인
7. WebSocket voice chat에서 `session_started`, `final_transcript`, `persona_text`, `persona_audio`, `session_ended` 확인

### StoryBook/Share 데모

1. interview session 생성
2. 질문 생성과 답변 저장
3. storybook 생성
4. chapter 목록 확인
5. share consent 생성
6. share link 생성
7. public share URL 조회
8. share link 비활성화 후 접근 차단 확인

### Deletion 데모

1. photo memory 또는 target media 생성
2. deletion request 생성
3. 파일 삭제와 DB 상태 변경 확인
4. deletion request 목록/상세 확인
5. audit log 확인

## GitHub Actions

Workflow: `.github/workflows/backend-test.yml`

동작:

1. `main`, `develop` push/pull_request에서 실행
2. Ubuntu runner 사용
3. MySQL 8.0 service container 실행
4. Python 3.12 설치
5. `pip install -r requirements.txt`
6. `.env` 생성
7. `alembic upgrade head`
8. `pytest -v`

확인할 것:

- MySQL service health check가 통과하는지
- `.env`의 DB 계정과 workflow service 계정이 일치하는지
- migration head가 하나인지
- mock provider 설정으로 외부 AI dependency가 필요 없는지

## 수동 점검

릴리스 전 최소 확인:

```powershell
alembic heads
alembic upgrade head
pytest -v
python -m uvicorn app.main:app --reload --port 8000
```

브라우저 확인:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
