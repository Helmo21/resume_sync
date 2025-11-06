"""
Service Account Manager with Rate Limiting and Rotation
Manages LinkedIn service accounts used for scraping profiles and jobs.

Risk Mitigation:
- LinkedIn blocks accounts → Automatic rotation, rate limiting
- Service degradation → Cooldown periods after failures
- Account exhaustion → Round-robin with fair distribution
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from ..models.linkedin_service_account import LinkedInServiceAccount
from ..core.encryption import get_encryption_service


class ServiceAccountManager:
    """Manager for LinkedIn service accounts with intelligent rotation"""

    # Rate limiting constants
    DAILY_REQUEST_LIMIT = 100  # Max requests per account per day
    COOLDOWN_MINUTES = 30  # Cooldown after failure

    @staticmethod
    def get_available_account(db: Session) -> Tuple[str, str]:
        """
        Get credentials for an available service account with smart selection.

        Enhanced selection strategy:
        1. Filter active accounts
        2. Exclude accounts over daily limit
        3. Exclude accounts in cooldown (recently failed)
        4. Prefer least-recently-used account (round-robin)
        5. Prefer premium accounts if available

        Args:
            db: Database session

        Returns:
            Tuple of (email, password) - decrypted

        Raises:
            Exception: If no active accounts available or all rate-limited
        """
        now = datetime.utcnow()
        cooldown_threshold = now - timedelta(minutes=ServiceAccountManager.COOLDOWN_MINUTES)

        # Query active accounts that are:
        # - Active
        # - Under daily limit
        # - Not in cooldown period
        available_accounts = db.query(LinkedInServiceAccount).filter(
            and_(
                LinkedInServiceAccount.is_active == True,
                or_(
                    LinkedInServiceAccount.requests_count_today < ServiceAccountManager.DAILY_REQUEST_LIMIT,
                    LinkedInServiceAccount.requests_count_today == None
                ),
                or_(
                    LinkedInServiceAccount.last_used_at < cooldown_threshold,
                    LinkedInServiceAccount.last_used_at == None
                )
            )
        ).order_by(
            # Order by: premium first, then least recently used
            LinkedInServiceAccount.is_premium.desc(),
            LinkedInServiceAccount.last_used_at.asc().nullsfirst()
        ).all()

        if not available_accounts:
            # Check if all accounts are rate limited
            rate_limited_count = db.query(LinkedInServiceAccount).filter(
                LinkedInServiceAccount.is_active == True,
                LinkedInServiceAccount.requests_count_today >= ServiceAccountManager.DAILY_REQUEST_LIMIT
            ).count()

            if rate_limited_count > 0:
                raise Exception(
                    f"All {rate_limited_count} service accounts have reached daily rate limit. "
                    f"Please wait or add more accounts."
                )

            # Check if accounts are in cooldown
            cooldown_count = db.query(LinkedInServiceAccount).filter(
                LinkedInServiceAccount.is_active == True,
                LinkedInServiceAccount.last_used_at >= cooldown_threshold
            ).count()

            if cooldown_count > 0:
                raise Exception(
                    f"All accounts are in cooldown period. "
                    f"Please wait {ServiceAccountManager.COOLDOWN_MINUTES} minutes or add more accounts."
                )

            raise Exception(
                "No LinkedIn service accounts available. "
                "Please add a service account using the CLI tool."
            )

        # Select first available account (best match based on ordering)
        account = available_accounts[0]

        # Log selection
        encryption_service = get_encryption_service()
        try:
            email = encryption_service.decrypt(account.email)
            masked_email = f"{email.split('@')[0][0]}***@{email.split('@')[1]}"
            print(f"📧 Selected service account: {masked_email} (used {account.requests_count_today}/{ServiceAccountManager.DAILY_REQUEST_LIMIT} times today)")
        except:
            print("📧 Selected service account")

        # Update usage stats
        account.last_used_at = now
        account.requests_count_today = (account.requests_count_today or 0) + 1
        db.commit()

        # Decrypt credentials
        try:
            email = encryption_service.decrypt(account.email)
            password = encryption_service.decrypt(account.password)
            return (email, password)
        except Exception as e:
            raise Exception(f"Failed to decrypt service account credentials: {str(e)}")

    @staticmethod
    def mark_account_failed(db: Session, email: str):
        """
        Mark an account as temporarily failed (triggers cooldown).

        This is called when login fails or account is detected/blocked.
        The account will be put in cooldown and not selected for COOLDOWN_MINUTES.

        Args:
            db: Database session
            email: Email of the failed account (encrypted)
        """
        encryption_service = get_encryption_service()

        # Find account by encrypted email (we need to check all)
        accounts = db.query(LinkedInServiceAccount).filter(
            LinkedInServiceAccount.is_active == True
        ).all()

        for account in accounts:
            try:
                decrypted_email = encryption_service.decrypt(account.email)
                if decrypted_email == email:
                    # Update last_used_at to trigger cooldown
                    account.last_used_at = datetime.utcnow()
                    db.commit()
                    print(f"⚠️  Account {email} marked as failed - entering {ServiceAccountManager.COOLDOWN_MINUTES}min cooldown")
                    return
            except:
                continue

    @staticmethod
    def get_account_stats(db: Session) -> dict:
        """
        Get statistics about service account usage.

        Returns:
            Dict with account stats
        """
        total_accounts = db.query(LinkedInServiceAccount).filter(
            LinkedInServiceAccount.is_active == True
        ).count()

        rate_limited = db.query(LinkedInServiceAccount).filter(
            LinkedInServiceAccount.is_active == True,
            LinkedInServiceAccount.requests_count_today >= ServiceAccountManager.DAILY_REQUEST_LIMIT
        ).count()

        now = datetime.utcnow()
        cooldown_threshold = now - timedelta(minutes=ServiceAccountManager.COOLDOWN_MINUTES)
        in_cooldown = db.query(LinkedInServiceAccount).filter(
            LinkedInServiceAccount.is_active == True,
            LinkedInServiceAccount.last_used_at >= cooldown_threshold
        ).count()

        available = total_accounts - rate_limited - in_cooldown

        return {
            "total_active": total_accounts,
            "available": max(0, available),
            "rate_limited": rate_limited,
            "in_cooldown": in_cooldown,
            "daily_limit_per_account": ServiceAccountManager.DAILY_REQUEST_LIMIT,
            "cooldown_minutes": ServiceAccountManager.COOLDOWN_MINUTES
        }

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
