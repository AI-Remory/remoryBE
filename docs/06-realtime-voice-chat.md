# 06. Realtime Voice Chat

## 목차

- [WebSocket Endpoint](#websocket-endpoint)
- [인증과 권한](#인증과-권한)
- [Message Protocol](#message-protocol)
- [처리 흐름](#처리-흐름)
- [STT/TTS/VoiceClone](#sttttsvoiceclone)
- [저장 규칙](#저장-규칙)
- [제한사항](#제한사항)
- [Frontend 예시](#frontend-예시)
- [TODO](#todo)

## WebSocket Endpoint

```text
WS /api/v1/ws/personas/{persona_id}/voice?token={access_token}
```

첫 구현은 초저지연 streaming이 아니라 chunked turn-taking이다.

```text
audio chunk 수신
  -> end_utterance
  -> STT
  -> Gemini persona reply
  -> TTS/VoiceClone
  -> audio URL 반환
```

## 인증과 권한

- `token` query param으로 access JWT를 전달한다.
- token이 없거나 유효하지 않으면 WebSocket을 close한다.
- 인증된 사용자가 persona owner여야 한다.
- `start` 처리 시 verification, consent, voice profile, usage/rate limit을 확인한다.

## Message Protocol

Client -> Server:

```json
{"type": "start", "chat_id": 1}
{"type": "audio_chunk", "data": "base64...", "mime_type": "audio/webm"}
{"type": "end_utterance"}
{"type": "stop"}
```

`chat_id`는 optional이다. 없으면 서버가 voice call용 persona chat을 만든다.

Server -> Client:

```json
{"type": "session_started", "session_id": 1}
{"type": "partial_transcript", "text": "..."}
{"type": "final_transcript", "text": "..."}
{"type": "persona_text", "text": "..."}
{"type": "persona_audio", "audio_url": "...", "audio_file_path": "..."}
{"type": "error", "message": "..."}
{"type": "session_ended"}
```

`partial_transcript`는 추후 streaming STT 확장을 위해 예약돼 있다.

## 처리 흐름

### start

1. `VoiceCallSession` 생성
2. persona owner 확인
3. target verification `APPROVED` 확인
4. `voice_cloning_consent`와 `voice_upload_consent` active 확인
5. `PersonaVoiceProfile.status == READY` 확인
6. target voice media 존재 확인
7. `RateLimitService`와 usage limit 확인
8. `VOICE_CALL_STARTED` audit log 기록
9. `session_started` event 전송

### audio_chunk

1. base64 decode
2. chunk 크기 제한 확인
3. utterance당 chunk 수 제한 확인
4. memory buffer에 누적
5. 비정상 요청은 error event와 `ABNORMAL_REQUEST_BLOCKED` audit log로 처리

### end_utterance

1. 누적 buffer를 `uploads/voices/call_inputs/{user_id}/`에 저장
2. STT 실행
3. USER `PersonaMessage` 저장
4. Gemini persona 응답 생성
5. PERSONA `PersonaMessage` 저장
6. VoiceClone 우선 시도, 실패 시 TTS fallback
7. 출력 음성을 `uploads/voices/call_outputs/{user_id}/`에 저장
8. `final_transcript`, `persona_text`, `persona_audio` event 전송
9. STT/voice generation usage count 증가

### stop

1. session status를 `ENDED`로 변경
2. `ended_at`, `total_duration_seconds` 저장
3. voice call seconds usage 증가
4. `VOICE_CALL_ENDED` audit log 기록
5. `session_ended` event 전송

## STT/TTS/VoiceClone

서비스 파일:

- `app/services/stt_service.py`
- `app/services/tts_service.py`
- `app/services/voice_clone_service.py`
- 실제 구현 export 위치: `app/services/speech/`

규칙:

- provider 구조를 새로 분리하지 않는다.
- 테스트 환경에서는 mock 결과를 반환한다.
- 실제 모델 또는 외부 dependency가 없어도 서버가 죽지 않도록 fallback한다.
- Gemini 실패 시 persona fallback text를 반환한다.
- TTS/VoiceClone 실패 시 `persona_text`는 반환하고 `persona_audio`는 `null`일 수 있다.

## 저장 규칙

사용자 음성 message:

- `sender_type = USER`
- `message_type = AUDIO`
- `content = STT 결과 텍스트`
- `audio_file_path = 입력 음성 파일 경로`

Persona 응답 message:

- `sender_type = PERSONA`
- `message_type = AUDIO`
- `content = Gemini 응답 텍스트`
- `audio_file_path = 생성 음성 파일 경로`
- `is_ai_generated = true`

## 제한사항

- 현재는 utterance 단위 처리이며 실시간 partial STT는 아직 없다.
- audio chunk는 base64 JSON message로 전달한다.
- 로컬 `uploads` storage를 유지한다.
- per-user active WebSocket 연결 수 제한이 있다.
- per-utterance chunk size/count 제한이 있다.
- per-minute utterance 제한이 있다.
- monthly STT, voice generation, persona voice generation, voice call seconds limit이 있다.

## Frontend 예시

```ts
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/personas/${personaId}/voice?token=${accessToken}`
);

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "start", chat_id: chatId }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === "persona_audio" && message.audio_url) {
    new Audio(message.audio_url).play();
  }
};

function sendAudioBlob(blob: Blob) {
  const reader = new FileReader();
  reader.onload = () => {
    const base64 = String(reader.result).split(",")[1];
    ws.send(JSON.stringify({ type: "audio_chunk", data: base64, mime_type: blob.type }));
    ws.send(JSON.stringify({ type: "end_utterance" }));
  };
  reader.readAsDataURL(blob);
}

function stopCall() {
  ws.send(JSON.stringify({ type: "stop" }));
}
```

## TODO

- `transcribe_stream(...)` 추가
- `partial_transcript` 실시간 전송
- `synthesize_stream(...)` 또는 audio chunk response 추가
- browser MediaRecorder chunk 크기 튜닝
- reconnect 정책과 session resume 정책 설계
