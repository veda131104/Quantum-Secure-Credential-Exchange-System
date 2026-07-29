"""
Biometric service for face recognition using DeepFace
"""

from deepface import DeepFace
import numpy as np
import base64
import io
import hashlib
from PIL import Image
from typing import List, Dict, Optional
from pathlib import Path

from app.core.config import settings


class FaceRecognitionService:
    """Service for face recognition and biometric operations"""

    def __init__(self):
        self.model_name = settings.BIOMETRIC_MODEL
        self.threshold = settings.BIOMETRIC_THRESHOLD
        self.embeddings_dir = Path(settings.BIOMETRIC_EMBEDDINGS_DIR)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

    def extract_embedding(self, image_data: bytes) -> np.ndarray:
        """
        Extract face embedding from image

        Args:
            image_data: Image data as bytes

        Returns:
            Embedding as numpy array
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Save temporarily (DeepFace works with file paths)
            temp_path = self.embeddings_dir / "temp_image.jpg"
            image.save(temp_path)

            # Extract embedding
            embedding_objs = DeepFace.represent(
                img_path=str(temp_path),
                model_name=self.model_name,
                enforce_detection=True,
            )

            # Clean up temp file
            temp_path.unlink()

            if not embedding_objs or len(embedding_objs) == 0:
                raise ValueError("No face detected in image")

            # Get the first face embedding
            embedding = np.array(embedding_objs[0]["embedding"])
            return embedding

        except Exception as e:
            raise Exception(f"Failed to extract face embedding: {str(e)}")

    def extract_embedding_from_base64(self, base64_data: str) -> np.ndarray:
        """
        Extract face embedding from base64 encoded image

        Args:
            base64_data: Base64 encoded image

        Returns:
            Embedding as numpy array
        """
        try:
            image_data = base64.b64decode(base64_data)
            return self.extract_embedding(image_data)
        except Exception as e:
            raise Exception(f"Failed to extract embedding from base64: {str(e)}")

    def hash_embedding(self, embedding: np.ndarray) -> str:
        """
        Create hash of embedding for storage

        Args:
            embedding: Embedding array

        Returns:
            SHA-256 hash as hex string
        """
        embedding_bytes = embedding.tobytes()
        return hashlib.sha256(embedding_bytes).hexdigest()

    def save_embedding(self, user_id: str, embedding: np.ndarray) -> str:
        """
        Save embedding to file

        Args:
            user_id: User ID
            embedding: Embedding array

        Returns:
            File path
        """
        embedding_file = self.embeddings_dir / f"{user_id}.npy"
        np.save(embedding_file, embedding)
        return str(embedding_file)

    def load_embedding(self, user_id: str) -> Optional[np.ndarray]:
        """
        Load embedding from file

        Args:
            user_id: User ID

        Returns:
            Embedding array or None if not found
        """
        embedding_file = self.embeddings_dir / f"{user_id}.npy"
        if not embedding_file.exists():
            return None

        return np.load(embedding_file)

    def compare_embeddings(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> Dict[str, float]:
        """
        Compare two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Dictionary with distance and verified status
        """
        try:
            # Calculate Euclidean distance
            distance = np.linalg.norm(embedding1 - embedding2)

            # Calculate cosine similarity
            cosine_similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )

            # Verify based on threshold
            verified = distance < self.threshold

            return {
                "distance": float(distance),
                "cosine_similarity": float(cosine_similarity),
                "verified": verified,
                "threshold": self.threshold,
            }
        except Exception as e:
            raise Exception(f"Failed to compare embeddings: {str(e)}")

    def verify_face(self, image_data: bytes, user_id: str) -> Dict[str, any]:
        """
        Verify a face against stored embedding

        Args:
            image_data: Image data as bytes
            user_id: User ID to verify against

        Returns:
            Verification result
        """
        try:
            # Extract embedding from provided image
            new_embedding = self.extract_embedding(image_data)

            # Load stored embedding
            stored_embedding = self.load_embedding(user_id)
            if stored_embedding is None:
                return {
                    "verified": False,
                    "message": "No biometric enrollment found for user",
                }

            # Compare embeddings
            comparison = self.compare_embeddings(stored_embedding, new_embedding)

            return {
                "verified": comparison["verified"],
                "distance": comparison["distance"],
                "cosine_similarity": comparison["cosine_similarity"],
                "threshold": comparison["threshold"],
                "message": "Face verified successfully"
                if comparison["verified"]
                else "Face verification failed",
            }
        except Exception as e:
            return {
                "verified": False,
                "message": f"Verification error: {str(e)}",
            }

    def verify_face_from_base64(self, base64_data: str, user_id: str) -> Dict[str, any]:
        """
        Verify face from base64 encoded image

        Args:
            base64_data: Base64 encoded image
            user_id: User ID to verify against

        Returns:
            Verification result
        """
        try:
            image_data = base64.b64decode(base64_data)
            return self.verify_face(image_data, user_id)
        except Exception as e:
            return {
                "verified": False,
                "message": f"Verification error: {str(e)}",
            }

    def detect_faces(self, image_data: bytes) -> List[Dict]:
        """
        Detect faces in an image

        Args:
            image_data: Image data as bytes

        Returns:
            List of detected faces with coordinates
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Save temporarily
            temp_path = self.embeddings_dir / "temp_detect.jpg"
            image.save(temp_path)

            # Detect faces
            faces = DeepFace.extract_faces(
                img_path=str(temp_path),
                enforce_detection=True,
                detector_backend="opencv",
            )

            # Clean up
            temp_path.unlink()

            return [
                {
                    "facial_area": face.get("facial_area"),
                    "confidence": face.get("confidence"),
                }
                for face in faces
            ]
        except Exception as e:
            raise Exception(f"Failed to detect faces: {str(e)}")

    def embedding_exists(self, user_id: str) -> bool:
        """Check if embedding exists for user"""
        embedding_file = self.embeddings_dir / f"{user_id}.npy"
        return embedding_file.exists()

    def delete_embedding(self, user_id: str) -> bool:
        """Delete embedding file for user"""
        embedding_file = self.embeddings_dir / f"{user_id}.npy"
        if embedding_file.exists():
            embedding_file.unlink()
            return True
        return False


# Singleton instance
face_recognition_service = FaceRecognitionService()
