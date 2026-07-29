"""
Pytest configuration and fixtures for DigiLocker 2.0 PQC testing
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil
from typing import Generator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.models.base import Base
from app.models.user import User
from app.models.issuer import Issuer
from app.models.credential import Credential
from app.services.pqc.dilithium_service import pqc_service
from app.main import app


# Test Database Configuration
@pytest.fixture(scope="session")
def test_db_engine():
    """Create in-memory SQLite database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# FastAPI Test Client
@pytest.fixture(scope="module")
def test_client():
    """Create FastAPI test client"""
    with TestClient(app) as client:
        yield client


# Temporary Directory for Test Keys
@pytest.fixture(scope="session")
def test_keys_dir():
    """Create temporary directory for test PQC keys"""
    temp_dir = tempfile.mkdtemp(prefix="pqc_test_keys_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# PQC Service Fixtures
@pytest.fixture
def test_pqc_keypair(test_keys_dir):
    """Generate a test PQC keypair"""
    identifier = "test_issuer_001"
    public_key, private_key, key_id = pqc_service.generate_keypair(
        identifier=identifier,
        keys_dir=test_keys_dir
    )

    return {
        "identifier": identifier,
        "public_key": public_key,
        "private_key": private_key,
        "key_id": key_id,
        "keys_dir": test_keys_dir
    }


@pytest.fixture
def test_pqc_keypair_2(test_keys_dir):
    """Generate a second test PQC keypair for multi-issuer tests"""
    identifier = "test_issuer_002"
    public_key, private_key, key_id = pqc_service.generate_keypair(
        identifier=identifier,
        keys_dir=test_keys_dir
    )

    return {
        "identifier": identifier,
        "public_key": public_key,
        "private_key": private_key,
        "key_id": key_id,
        "keys_dir": test_keys_dir
    }


@pytest.fixture
def test_credential_data():
    """Sample credential data for testing"""
    return {
        "user_id": "test-user-123",
        "issuer_id": "test-issuer-456",
        "credential_type": "degree",
        "credential_name": "Bachelor of Science in Computer Science",
        "credential_number": "DEG-2024-001",
        "ipfs_cid": "QmTest123456789",
        "metadata": {
            "university": "Test University",
            "graduation_date": "2024-05-15",
            "grade": "First Class Honors"
        }
    }


# User Fixtures
@pytest.fixture
def test_user(test_db: Session):
    """Create a test user in the database"""
    user = User(
        id="test-user-123",
        email="testuser@example.com",
        username="testuser",
        hashed_password="$2b$12$test_hashed_password",
        full_name="Test User",
        wallet_address="0x1234567890123456789012345678901234567890",
        is_active=True,
        is_verified=True,
        role="user"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_issuer(test_db: Session, test_pqc_keypair):
    """Create a test issuer in the database"""
    # First create issuer user
    issuer_user = User(
        id="test-issuer-user-456",
        email="issuer@testuniversity.edu",
        username="testuniversity",
        hashed_password="$2b$12$test_hashed_password",
        full_name="Test University Registrar",
        is_active=True,
        is_verified=True,
        role="issuer"
    )
    test_db.add(issuer_user)
    test_db.commit()

    # Create issuer
    issuer = Issuer(
        id="test-issuer-456",
        user_id=issuer_user.id,
        organization_name="Test University",
        organization_type="university",
        registration_number="TEST-UNI-001",
        contact_email="registrar@testuniversity.edu",
        contact_phone="+1234567890",
        blockchain_address="0xabcdef1234567890abcdef1234567890abcdef12",
        pqc_public_key=test_pqc_keypair["public_key"],
        pqc_key_id=test_pqc_keypair["key_id"],
        is_approved=True,
        is_active=True
    )
    test_db.add(issuer)
    test_db.commit()
    test_db.refresh(issuer)
    return issuer


@pytest.fixture
def test_credential(test_db: Session, test_user, test_issuer, test_pqc_keypair, test_credential_data):
    """Create a test credential with valid PQC signature"""
    # Hash the credential data
    credential_data_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
    credential_hash_bytes = pqc_service.hash_data(credential_data_str)
    credential_hash = credential_hash_bytes.hex()

    # Sign the hash
    signature = pqc_service.sign_data(
        data=credential_hash_bytes,
        private_key_hex=test_pqc_keypair["private_key"]
    )

    # Create credential
    credential = Credential(
        id="test-credential-789",
        user_id=test_user.id,
        issuer_id=test_issuer.id,
        credential_type=test_credential_data["credential_type"],
        credential_name=test_credential_data["credential_name"],
        credential_number=test_credential_data["credential_number"],
        credential_hash=credential_hash,
        pqc_signature=signature,
        signature_algorithm="Dilithium2",
        ipfs_cid=test_credential_data["ipfs_cid"],
        credential_metadata=test_credential_data["metadata"],
        issue_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=365),
        is_active=True,
        is_revoked=False
    )
    test_db.add(credential)
    test_db.commit()
    test_db.refresh(credential)
    return credential


# Results Collection for Visualization
@pytest.fixture(scope="session")
def test_results_collector():
    """Collect test results for visualization"""
    results = {
        "attack_scenarios": [],
        "timing_measurements": [],
        "validation_tests": [],
        "performance_metrics": [],
        "security_events": []
    }
    yield results


# Visualization Output Directory
@pytest.fixture(scope="session")
def test_output_dir():
    """Create output directory for test visualizations"""
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    yield output_dir


# Pytest Configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "attack: mark test as an attack simulation"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance benchmark"
    )
    config.addinivalue_line(
        "markers", "visualization: mark test as generating visualizations"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
