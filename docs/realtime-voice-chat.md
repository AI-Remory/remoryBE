# Realtime Voice Chat

## WebSocket URL

`WS /api/v1/ws/personas/{persona_id}/voice?token={access_token}`

`token` is the normal access JWT. The server rejects the connection when the token is missing, invalid, expired, or when the authenticated user does not own the persona.

## Client Messages

```json
{"type": "start", "chat_id": 1}
{"type": "audio_chunk", "data": "base64...", "mime_type": "audio/webm"}
{"type": "end_utterance"}
{"type": "stop"}
```

`chat_id` is optional. If it is omitted, the server creates a persona chat for the call.

## Server Messages

```json
{"type": "session_started", "session_id": 1}
{"type": "partial_transcript", "text": "..."}
{"type": "final_transcript", "text": "..."}
{"type": "persona_text", "text": "..."}
{"type": "persona_audio", "audio_url": "...", "audio_file_path": "..."}
{"type": "error", "message": "..."}
{"type": "session_ended"}
```

The first implementation is chunked turn-taking, not ultra-low-latency streaming. `partial_transcript` is reserved for a later streaming STT path.

## Flow

1. Client opens the WebSocket with `token`.
2. Client sends `start`.
3. Server creates `VoiceCallSession` and validates owner, approved verification, active voice cloning consent, READY voice profile, target voice media, rate limits, and usage limits.
4. Client sends one or more base64 `audio_chunk` messages.
5. Client sends `end_utterance`.
6. Server stores input audio under `uploads/voices/call_inputs/`, runs STT, stores the USER audio message, generates the persona reply with Gemini, stores the PERSONA audio message, synthesizes audio under `uploads/voices/call_outputs/`, and sends transcript/text/audio events.
7. Client sends `stop`.
8. Server marks the session ENDED, records audit logs, and increments voice call usage.

## Frontend Example

```ts
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/personas/${personaId}/voice?token=${accessToken}`
);

ws.onopen = () => ws.send(JSON.stringify({ type: "start", chat_id: chatId }));
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

## Limits

- Per-user active WebSocket connection limit.
- Per-utterance chunk size and chunk count limits.
- Per-minute utterance limit.
- Monthly STT, voice generation, persona voice generation, and voice call seconds limits.
- The server keeps the existing local `uploads` storage layout.

## Streaming TODO

- Add streaming STT implementation behind `transcribe_stream(...)`.
- Emit `partial_transcript` as interim STT results arrive.
- Add streaming TTS or chunked audio synthesis behind a separate `synthesize_stream(...)`.
- Keep the public WebSocket protocol compatible by adding optional server audio chunk events.
