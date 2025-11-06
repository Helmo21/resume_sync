"""
Auto-load LinkedIn Service Accounts from Environment Variables
This runs on application startup to sync .env credentials with database
"""
import os
from sqlalchemy.orm import Session
from ..models.linkedin_service_account import LinkedInServiceAccount
from ..services.service_account_manager import ServiceAccountManager
from ..core.encryption import get_encryption_service
import uuid


def load_service_accounts_from_env(db: Session) -> dict:
    """
    Load LinkedIn service accounts from LINKEDIN_SERVICE_ACCOUNTS env var.

    Format: "email1:password1|email2:password2|email3:password3"
    Premium accounts: "email1,email2" in LINKEDIN_PREMIUM_ACCOUNTS

    Returns:
        {
            "loaded": 2,
            "existing": 1,
            "failed": 0,
            "accounts": [...]
        }
    """
    accounts_env = os.getenv("LINKEDIN_SERVICE_ACCOUNTS", "")
    premium_env = os.getenv("LINKEDIN_PREMIUM_ACCOUNTS", "")

    if not accounts_env or accounts_env == "linkedin_bot1@example.com:password123|linkedin_bot2@example.com:password456":
        print("⚠️  No LinkedIn service accounts configured in .env")
        print("   Please set LINKEDIN_SERVICE_ACCOUNTS in backend/.env")
        return {
            "loaded": 0,
            "existing": 0,
            "failed": 0,
            "error": "No accounts configured (using example values)"
        }

    # Parse premium accounts
    premium_emails = set()
    if premium_env:
        premium_emails = set(email.strip() for email in premium_env.split(","))

    # Parse service accounts
    account_pairs = accounts_env.split("|")

    results = {
        "loaded": 0,
        "existing": 0,
        "failed": 0,
        "accounts": []
    }

    encryption_service = get_encryption_service()

    for pair in account_pairs:
        if not pair.strip():
            continue

        try:
            if ":" not in pair:
                print(f"⚠️  Invalid format (missing :): {pair[:20]}...")
                results["failed"] += 1
                continue

            email, password = pair.split(":", 1)
            email = email.strip()
            password = password.strip()

            if not email or not password:
                print(f"⚠️  Empty email or password: {email}")
                results["failed"] += 1
                continue

            # Check if account already exists
            encrypted_email = encryption_service.encrypt(email)
            existing = db.query(LinkedInServiceAccount).filter(
                LinkedInServiceAccount.email == encrypted_email
            ).first()

            if existing:
                print(f"ℹ️  Account already exists: {email[:3]}***@{email.split('@')[1]}")
                results["existing"] += 1
                results["accounts"].append({
                    "email": email,
                    "status": "existing",
                    "is_premium": existing.is_premium
                })
                continue

            # Add new account
            is_premium = email in premium_emails

            try:
                ServiceAccountManager.add_account(
                    db=db,
                    email=email,
                    password=password,
                    is_premium=is_premium,
                    is_active=True
                )

                masked_email = f"{email[:3]}***@{email.split('@')[1]}"
                premium_badge = " [PREMIUM]" if is_premium else ""
                print(f"✅ Loaded service account: {masked_email}{premium_badge}")

                results["loaded"] += 1
                results["accounts"].append({
                    "email": email,
                    "status": "loaded",
                    "is_premium": is_premium
                })

            except Exception as e:
                print(f"❌ Failed to add account {email}: {str(e)}")
                results["failed"] += 1

        except Exception as e:
            print(f"❌ Error processing account pair: {str(e)}")
            results["failed"] += 1

    # Summary
    print(f"\n📊 Service Account Summary:")
    print(f"   ✅ Loaded: {results['loaded']}")
    print(f"   ℹ️  Already exists: {results['existing']}")
    print(f"   ❌ Failed: {results['failed']}")

    return results


def verify_service_accounts(db: Session) -> dict:
    """
    Verify service accounts are available and healthy

    Returns:
        Stats about service account availability
    """
    total = db.query(LinkedInServiceAccount).filter(
        LinkedInServiceAccount.is_active == True
    ).count()

    if total == 0:
        print("\n⚠️  WARNING: No active service accounts found!")
        print("   Job scraping will fail until accounts are added.")
        print("   Please configure LINKEDIN_SERVICE_ACCOUNTS in backend/.env")
        return {
            "total": 0,
            "warning": "No accounts configured"
        }

    stats = ServiceAccountManager.get_account_stats(db)

    print(f"\n🔐 Service Accounts Status:")
    print(f"   Total active: {stats['total_active']}")
    print(f"   Available now: {stats['available']}")
    print(f"   Rate limited: {stats['rate_limited']}")
    print(f"   In cooldown: {stats['in_cooldown']}")

    if stats['available'] == 0:
        print("\n⚠️  WARNING: No accounts currently available!")
        if stats['rate_limited'] > 0:
            print(f"   {stats['rate_limited']} account(s) hit daily limit")
        if stats['in_cooldown'] > 0:
            print(f"   {stats['in_cooldown']} account(s) in cooldown period")

    return stats
