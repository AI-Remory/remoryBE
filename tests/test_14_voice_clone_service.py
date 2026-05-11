import asyncio

from app.models.persona import PersonaVoiceProfile, VoiceProfileStatus
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
