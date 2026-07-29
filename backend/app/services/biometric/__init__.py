"""Biometric Service"""

from app.services.biometric.face_recognition_service import (
    FaceRecognitionService,
    face_recognition_service,
)

__all__ = ["FaceRecognitionService", "face_recognition_service"]
