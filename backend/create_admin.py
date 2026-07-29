#!/usr/bin/env python3
"""
Create an admin user for DigiLocker 2.0
Run this script once to set up the initial admin account
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.base import SessionLocal, init_db
from app.models import User
from app.core.security import hash_password
import uuid
from datetime import datetime


def create_admin():
    """Create an admin user"""
    print("🚀 DigiLocker 2.0 - Admin User Setup")
    print("=" * 50)

    # Initialize database
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return

    db = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("\n⚠️  Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")

            choice = input("\nDo you want to reset the password? (yes/no): ").strip().lower()
            if choice == "yes":
                new_password = "Admin@123"
                existing_admin.hashed_password = hash_password(new_password)
                existing_admin.is_active = True
                existing_admin.role = "admin"
                db.commit()
                print(f"\n✓ Admin password reset to: {new_password}")
                print("  Please change this password after logging in!")
            return

        # Create admin user
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@digilocker.com",
            username="admin",
            hashed_password=hash_password("Admin@123"),
            full_name="System Administrator",
            role="admin",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )

        db.add(admin)
        db.commit()

        print("\n✓ Admin user created successfully!")
        print("\n" + "=" * 50)
        print("📝 Admin Credentials:")
        print("=" * 50)
        print(f"   Username: admin")
        print(f"   Password: Admin@123")
        print(f"   Email:    admin@digilocker.com")
        print("=" * 50)
        print("\n⚠️  IMPORTANT: Please change this password after first login!")
        print("\n🌐 You can now:")
        print("   1. Login at: http://localhost:3000/login")
        print("   2. Register issuers via API: POST /api/v1/issuers/register")
        print("\n")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
