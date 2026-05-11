import asyncio

from app.services.speech import FasterWhisperSTTService, MockSTTService, STTResult, get_stt_service


def test_mock_stt_service_returns_deterministic_result():
    result = asyncio.run(MockSTTService().transcribe("unused.wav"))

    assert isinstance(result, STTResult)
    assert result.text == "테스트용 음성 변환 결과입니다."
    assert result.language == "ko"
    assert result.duration_seconds is None


def test_get_stt_service_uses_mock_under_pytest():
    assert isinstance(get_stt_service(), MockSTTService)


def test_faster_whisper_service_is_lazy_loaded():
    service = FasterWhisperSTTService(model_size="base")

    assert service.model_size == "base"
    assert service._model is None
