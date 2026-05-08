"""프로젝트 상수"""

# 파일 업로드
MAX_UPLOAD_SIZE = 52428800  # 50MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

# 업로드 경로
UPLOAD_DIR = "./uploads"
IMAGES_DIR = f"{UPLOAD_DIR}/images"
VOICES_DIR = f"{UPLOAD_DIR}/voices"

# API 응답 메시지
SUCCESS_MESSAGE = "Success"
ERROR_MESSAGE = "Error occurred"

