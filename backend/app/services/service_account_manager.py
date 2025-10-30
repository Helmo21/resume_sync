"""
Service Account Manager
Manages LinkedIn service accounts used for scraping profiles and jobs.
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.linkedin_service_account import LinkedInServiceAccount
from ..core.encryption import get_encryption_service


class ServiceAccountManager:
    """Manager for LinkedIn service accounts"""

    @staticmethod
    def get_available_account(db: Session) -> Tuple[str, str]:
        """
        Get credentials for an available service account.

        Selection strategy (for now):
        - Pick the first active account
        - Update last_used_at timestamp
        - Increment request count

        Future enhancements:
        - Round-robin or least-recently-used
        - Rate limit checking
        - Premium account preference

        Args:
            db: Database session

        Returns:
            Tuple of (email, password) - decrypted

        Raises:
            Exception: If no active accounts available or decryption fails
        """
        # Get first active account
        account = db.query(LinkedInServiceAccount)\
            .filter(LinkedInServiceAccount.is_active == True)\
            .first()

        if not account:
            raise Exception(
                "No LinkedIn service accounts available. "
                "Please add a service account using the CLI tool."
            )

        # Update usage stats
        account.last_used_at = datetime.utcnow()
        account.requests_count_today += 1
        db.commit()

        # Decrypt credentials
        try:
            encryption_service = get_encryption_service()
            email = encryption_service.decrypt(account.email)
            password = encryption_service.decrypt(account.password)
            return (email, password)
        except Exception as e:
            raise Exception(f"Failed to decrypt service account credentials: {str(e)}")

    @staticmethod
    def add_account(
        db: Session,
        email: str,
        password: str,
        is_premium: bool = False,
        is_active: bool = True
    ) -> LinkedInServiceAccount:
        """
        Add a new service account.

        Args:
            db: Database session
            email: LinkedIn email (plaintext)
            password: LinkedIn password (plaintext)
            is_premium: Whether this is a premium account
            is_active: Whether this account is active

        Returns:
            Created LinkedInServiceAccount object

        Raises:
            Exception: If encryption or database insert fails
        """
        # Encrypt credentials
        try:
            encryption_service = get_encryption_service()
            encrypted_email = encryption_service.encrypt(email)
            encrypted_password = encryption_service.encrypt(password)
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

        # Create account
        try:
            import uuid
            account = LinkedInServiceAccount(
                id=uuid.uuid4(),
                email=encrypted_email,
                password=encrypted_password,
                is_premium=is_premium,
                is_active=is_active,
                last_used_at=None,
                requests_count_today=0,
                created_at=datetime.utcnow()
            )

            db.add(account)
            db.commit()
            db.refresh(account)

            return account
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to add service account: {str(e)}")

    @staticmethod
    def list_accounts(db: Session) -> list:
        """
        List all service accounts (with masked credentials).

        Args:
            db: Database session

        Returns:
            List of account dictionaries with masked credentials
        """
        accounts = db.query(LinkedInServiceAccount).all()

        result = []
        encryption_service = get_encryption_service()

        for account in accounts:
            try:
                # Decrypt and mask email
                decrypted_email = encryption_service.decrypt(account.email)
                parts = decrypted_email.split('@')
                if len(parts) == 2:
                    masked_email = f"{parts[0][0]}***@{parts[1]}"
                else:
                    masked_email = "***"
            except Exception:
                masked_email = "***"

            result.append({
                'id': str(account.id),
                'email': masked_email,
                'is_premium': account.is_premium,
                'is_active': account.is_active,
                'last_used_at': account.last_used_at,
                'requests_count_today': account.requests_count_today,
                'created_at': account.created_at
            })

        return result

    @staticmethod
    def deactivate_account(db: Session, account_id: str) -> bool:
        """
        Deactivate a service account (soft delete).

        Args:
            db: Database session
            account_id: UUID of account to deactivate

        Returns:
            True if successful

        Raises:
            Exception: If account not found
        """
        import uuid
        account = db.query(LinkedInServiceAccount)\
            .filter(LinkedInServiceAccount.id == uuid.UUID(account_id))\
            .first()

        if not account:
            raise Exception(f"Service account {account_id} not found")

        account.is_active = False
        db.commit()

        return True

    @staticmethod
    def reset_daily_counts(db: Session) -> int:
        """
        Reset request counts for all accounts (should be called daily).

        Args:
            db: Database session

        Returns:
            Number of accounts reset
        """
        count = db.query(LinkedInServiceAccount).update(
            {LinkedInServiceAccount.requests_count_today: 0}
        )
        db.commit()

        return count
