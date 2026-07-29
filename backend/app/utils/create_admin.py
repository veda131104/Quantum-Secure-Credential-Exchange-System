"""
Utility script to create the first admin user
Run this script to bootstrap the application with an admin account
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.models.base import SessionLocal, init_db
from app.models import User
from app.core.security import hash_password
from app.services.blockchain import blockchain_service
import getpass


def create_admin_user():
    """Create an admin user"""
    print("=" * 60)
    print("DigiLocker 2.0 - Admin User Creation")
    print("=" * 60)
    print()

    # Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized.\n")

    db: Session = SessionLocal()

    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
            response = input("Do you want to create another admin? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Exiting...")
                return

        # Get admin details
        print("Enter admin details:")
        print()

        email = input("Email: ").strip()
        if not email:
            print("Error: Email is required")
            return

        username = input("Username: ").strip()
        if not username:
            print("Error: Username is required")
            return

        password = getpass.getpass("Password: ")
        if not password or len(password) < 8:
            print("Error: Password must be at least 8 characters")
            return

        confirm_password = getpass.getpass("Confirm Password: ")
        if password != confirm_password:
            print("Error: Passwords do not match")
            return

        full_name = input("Full Name (optional): ").strip() or None
        phone = input("Phone (optional): ").strip() or None

        print()
        print("Creating blockchain wallet...")

        # Check if blockchain is connected
        if not blockchain_service.is_connected():
            print(
                "Warning: Blockchain not connected. Attempting to connect..."
            )
            blockchain_service.connect()

        if blockchain_service.is_connected():
            blockchain_account = blockchain_service.create_account()
            wallet_address = blockchain_account["address"]
            print(f"Wallet created: {wallet_address}")
        else:
            wallet_address = None
            print("Warning: Could not create blockchain wallet. Blockchain not connected.")

        # Check for existing user
        existing_user = (
            db.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )

        if existing_user:
            print(f"Error: User with this email or username already exists")
            return

        # Hash password
        hashed_pwd = hash_password(password)

        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            hashed_password=hashed_pwd,
            full_name=full_name,
            phone=phone,
            wallet_address=wallet_address,
            role="admin",
            is_active=True,
            is_verified=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print()
        print("=" * 60)
        print("Admin user created successfully!")
        print("=" * 60)
        print()
        print(f"User ID: {admin_user.id}")
        print(f"Email: {admin_user.email}")
        print(f"Username: {admin_user.username}")
        print(f"Role: {admin_user.role}")
        if wallet_address:
            print(f"Wallet Address: {wallet_address}")
        print()
        print("You can now login with these credentials.")
        print()

    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
