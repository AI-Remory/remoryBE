# 06. Realtime Voice Chat

## OpenVoice Runtime Notes (2026-05-15)

- Voice synthesis order at `end_utterance`:
  1. STT transcription
  2. LLM persona reply
  3. OpenVoice cloned synthesis (when profile provider is `openvoice`)
- Voice profile usage gates remain mandatory:
  - approved verification
  - `voice_upload_consent`
  - `voice_cloning_consent`
  - profile `status=READY`
  - review status `USER_CONFIRMED` or `ADMIN_APPROVED`
- OpenVoice configuration required in runtime:
  - `OPENVOICE_CONVERTER_CONFIG_PATH`
  - `OPENVOICE_CONVERTER_CHECKPOINT_PATH`
  - `OPENVOICE_SOURCE_SE_PATH`
  - `OPENVOICE_OUTPUT_DIR`
- Production behavior:
  - do not silently hide OpenVoice failures with mock synthesis
  - websocket responds with error when synthesis fails
- CPU/GPU:
  - `OPENVOICE_DEVICE=auto` chooses CUDA when available, otherwise CPU
  - set `OPENVOICE_DEVICE=cuda` only when CUDA runtime is verified

### OpenVoice Checkpoint Setup

1. Install OpenVoice runtime package and torch compatible with your CUDA/CPU.
2. Download OpenVoice V2 checkpoints.
3. Configure:
   - `OPENVOICE_CONVERTER_CONFIG_PATH`
   - `OPENVOICE_CONVERTER_CHECKPOINT_PATH`
   - `OPENVOICE_SOURCE_SE_PATH`
4. Ensure files exist before calling evaluate API.
5. If paths are invalid, evaluate returns `FAILED` with `error_message`.

## 목차

- [Endpoint](#endpoint)
- [인증과 권한](#인증과-권한)
- [Client Message](#client-message)
- [Server Message](#server-message)
- [처리 흐름](#처리-흐름)
- [저장 경로](#저장-경로)
- [제한값](#제한값)
- [Frontend 예시](#frontend-예시)

## Endpoint

```http
WS /api/v1/ws/personas/{persona_id}/voice?token=<access_token>
```

라우터는 `app/api/v1/endpoints/realtime_voice.py`, 핵심 로직은 `app/services/realtime_voice_service.py`에 있다.

## 인증과 권한

- query string `token`은 access token이어야 한다.
- token이 없거나 잘못되면 서버는 accept 전에 `WS_1008_POLICY_VIOLATION`으로 close한다.
- persona는 현재 사용자 소유 target의 persona여야 한다.

## Client Message

### start

```json
{
  "type": "start",
  "chat_id": 1
}
```

`chat_id`는 선택이다. 없으면 서버가 `Voice call` title의 chat을 만든다.

### audio_chunk

```json
{
  "type": "audio_chunk",
  "mime_type": "audio/webm",
  "data": "base64-encoded-audio"
}
```

`data`는 base64 문자열이다. 지원 확장자 매핑은 `audio/wav`, `audio/mpeg`, `audio/mp4`, 그 외 기본 `.webm`이다.

### end_utterance

```json
{
  "type": "end_utterance"
}
```

서버가 현재 buffer를 STT -> LLM persona reply -> cloned voice/TTS 순서로 처리한다.

### stop

```json
{
  "type": "stop"
}
```

세션 종료 후 서버가 `session_ended`를 보내고 정상 close한다.

## Server Message

| type | payload |
| --- | --- |
| `session_started` | `{ "type": "session_started", "session_id": 1 }` |
| `final_transcript` | `{ "type": "final_transcript", "text": "..." }` |
| `persona_text` | `{ "type": "persona_text", "text": "..." }` |
| `persona_audio` | `{ "type": "persona_audio", "audio_url": "...", "audio_file_path": "..." }` |
| `session_ended` | `{ "type": "session_ended" }` |
| `error` | `{ "type": "error", "message": "..." }` |

## 처리 흐름

1. `start` 수신: 사용자/사용량/persona 권한 확인, chat resolve, `VoiceCallSession` 생성, audit log 기록.
2. `audio_chunk` 수신: base64 decode, chunk 크기/개수 검증, buffer에 append.
3. `end_utterance` 수신: utterance rate limit 확인, STT/voice generation 한도 확인, input file 저장, 사용자 message 저장, persona reply 생성, voice clone 또는 TTS 출력 저장, persona message 저장.
4. `stop` 수신 또는 disconnect: session 종료, duration 계산, voice call usage 반영, audit log 기록.

## 저장 경로

`Settings.UPLOAD_DIR` 기준:

| 파일 | 경로 |
| --- | --- |
| 입력 음성 | `uploads/voices/call_inputs/{user_id}/input_*.webm|wav|mp3|m4a` |
| 출력 음성 | `uploads/voices/call_outputs/{user_id}/output_*.wav` |

REST chat audio endpoint는 별도 endpoint인 `POST /api/v1/chats/{chat_id}/audio`를 사용한다.

## 제한값

`app/core/settings.py` 기준:

| 설정 | 기본값 | 의미 |
| --- | --- | --- |
| `VOICE_WS_MAX_ACTIVE_CONNECTIONS_PER_USER` | `2` | 사용자별 동시 WebSocket |
| `VOICE_WS_MAX_UTTERANCES_PER_MINUTE` | `20` | 분당 utterance |
| `VOICE_WS_MAX_CHUNK_BYTES` | `262144` | chunk bytes |
| `VOICE_WS_MAX_CHUNKS_PER_UTTERANCE` | `100` | utterance별 chunk 수 |
| `MONTHLY_USER_STT_REQUEST_LIMIT` | `500` | 월 STT 요청 |
| `MONTHLY_USER_VOICE_GENERATION_LIMIT` | `1000` | 월 음성 생성 |
| `MONTHLY_PERSONA_VOICE_GENERATION_LIMIT` | `500` | persona별 월 음성 생성 |
| `MONTHLY_USER_VOICE_CALL_SECONDS_LIMIT` | `3600` | 월 음성 통화 초 |

## Frontend 예시

```ts
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/personas/${personaId}/voice?token=${accessToken}`,
);

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "start", chat_id: chatId }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === "final_transcript") renderTranscript(message.text);
  if (message.type === "persona_text") renderPersonaText(message.text);
  if (message.type === "persona_audio" && message.audio_url) playAudio(message.audio_url);
  if (message.type === "error") showError(message.message);
};

function sendChunk(bytes: Uint8Array, mimeType = "audio/webm") {
  const binary = Array.from(bytes, (b) => String.fromCharCode(b)).join("");
  ws.send(JSON.stringify({
    type: "audio_chunk",
    mime_type: mimeType,
    data: btoa(binary),
  }));
}

function endUtterance() {
  ws.send(JSON.stringify({ type: "end_utterance" }));
}

function stop() {
  ws.send(JSON.stringify({ type: "stop" }));
}
```
