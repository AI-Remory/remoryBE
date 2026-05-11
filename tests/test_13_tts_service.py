import asyncio

from app.services.speech import MeloTTSService, MockTTSService, TTSResult, get_tts_service


def test_mock_tts_service_creates_dummy_audio_file(tmp_path):
    output_path = tmp_path / "reply.wav"

    result = asyncio.run(MockTTSService().synthesize("hello", str(output_path)))

    assert isinstance(result, TTSResult)
    assert result.audio_file_path == str(output_path)
    assert result.provider == "mock"
    assert result.duration_seconds is None
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"RIFF")


def test_get_tts_service_uses_mock_under_pytest():
    assert isinstance(get_tts_service(), MockTTSService)


def test_melotts_service_is_lazy_loaded():
    service = MeloTTSService()

    assert service._models == {}
