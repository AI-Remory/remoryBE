import asyncio
from pathlib import Path

from app.models.persona import PersonaVoiceProfile, VoiceProfileStatus
from app.core.settings import settings
from app.services.speech import (
    MockVoiceCloneService,
    OpenVoiceV2VoiceCloneService,
    VoiceCloneResult,
    get_voice_clone_service,
)


def test_mock_voice_clone_service_creates_profile_metadata():
    result = asyncio.run(MockVoiceCloneService().create_voice_profile(1, ["a.wav", "b.wav"]))

    assert result["persona_id"] == 1
    assert result["provider"] == "mock"
    assert result["status"] == "READY"
    assert result["reference_audio_count"] == 2
    assert result["error_message"] is None


def test_mock_voice_clone_service_creates_dummy_audio_file(tmp_path):
    output_path = tmp_path / "voice.wav"

    result = asyncio.run(
        MockVoiceCloneService().synthesize_with_cloned_voice(
            "hello",
            {"persona_id": 1, "provider": "mock"},
            str(output_path),
        )
    )

    assert isinstance(result, VoiceCloneResult)
    assert result.audio_file_path == str(output_path)
    assert result.provider == "mock"
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"RIFF")


def test_get_voice_clone_service_uses_mock_under_pytest():
    assert isinstance(get_voice_clone_service(), MockVoiceCloneService)


def test_openvoice_service_is_lazy_loaded():
    service = OpenVoiceV2VoiceCloneService()

    assert service.model_name == "openvoice-v2"
    assert service._converter is None


def test_persona_voice_profile_model_has_voice_clone_state_fields():
    profile = PersonaVoiceProfile(
        persona_id=1,
        target_id=2,
        provider="mock",
        status=VoiceProfileStatus.PENDING,
        reference_audio_count=3,
    )

    assert profile.target_id == 2
    assert profile.provider == "mock"
    assert profile.status == VoiceProfileStatus.PENDING
    assert profile.reference_audio_count == 3


def test_openvoice_create_profile_returns_failed_when_config_missing(monkeypatch):
    monkeypatch.setattr(settings, "OPENVOICE_FAILOVER_TO_MOCK", False)
    service = OpenVoiceV2VoiceCloneService()

    payload = asyncio.run(service.create_voice_profile(10, ["missing.wav"]))

    assert payload["provider"] == "openvoice"
    assert payload["status"] == "FAILED"
    assert payload["error_message"]


def test_openvoice_synthesize_raises_when_profile_path_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "OPENVOICE_FAILOVER_TO_MOCK", False)
    service = OpenVoiceV2VoiceCloneService()
    output_path = tmp_path / "output.wav"

    async def _run():
        await service.synthesize_with_cloned_voice("hello", {"provider": "openvoice"}, str(output_path))

    try:
        asyncio.run(_run())
        raised = False
    except RuntimeError:
        raised = True

    assert raised is True


def test_openvoice_create_profile_success_payload_when_openvoice_service_is_mocked(monkeypatch, tmp_path):
    service = OpenVoiceV2VoiceCloneService()
    target_se = tmp_path / "target_se.pth"
    target_se.write_bytes(b"stub")

    def _fake_create_profile(persona_id, reference_audio_paths):
        return {
            "persona_id": persona_id,
            "provider": "openvoice",
            "model_name": "openvoice-v2",
            "status": "READY",
            "reference_audio_count": len(reference_audio_paths),
            "reference_audio_total_seconds": None,
            "voice_profile_path": str(target_se),
            "sample_audio_path": None,
            "error_message": None,
        }

    monkeypatch.setattr(service._openvoice, "create_profile", _fake_create_profile)
    payload = asyncio.run(service.create_voice_profile(33, ["ref.wav"]))

    assert payload["status"] == "READY"
    assert payload["provider"] == "openvoice"
    assert payload["voice_profile_path"] == str(target_se)


def test_openvoice_synthesize_success_when_openvoice_service_is_mocked(monkeypatch, tmp_path):
    service = OpenVoiceV2VoiceCloneService()
    output_path = tmp_path / "converted.wav"
    output_path.write_bytes(b"RIFFstub")

    def _fake_synthesize(text, voice_profile_path, output_path):
        return str(Path(output_path))

    monkeypatch.setattr(service._openvoice, "synthesize", _fake_synthesize)

    result = asyncio.run(
        service.synthesize_with_cloned_voice(
            "테스트",
            {"provider": "openvoice", "voice_profile_path": str(tmp_path / "target_se.pth")},
            str(output_path),
        )
    )

    assert result.provider == "openvoice"
    assert result.audio_file_path == str(output_path)
