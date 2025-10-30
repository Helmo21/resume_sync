#!/usr/bin/env python3
"""
CLI tool to add LinkedIn service accounts.

Usage:
    python scripts/add_service_account.py --email "account@example.com" --password "password123"
    python scripts/add_service_account.py --email "premium@example.com" --password "pass" --premium
    python scripts/add_service_account.py --list
"""
import sys
import os
import argparse

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.service_account_manager import ServiceAccountManager


def add_account(email: str, password: str, premium: bool = False):
    """Add a new service account"""
    db = SessionLocal()
    try:
        account = ServiceAccountManager.add_account(
            db=db,
            email=email,
            password=password,
            is_premium=premium,
            is_active=True
        )

        print(f"✅ Service account added successfully!")
        print(f"   ID: {account.id}")
        print(f"   Email: {email}")
        print(f"   Premium: {premium}")
        print(f"   Active: True")

    except Exception as e:
        print(f"❌ Failed to add service account: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


def list_accounts():
    """List all service accounts"""
    db = SessionLocal()
    try:
        accounts = ServiceAccountManager.list_accounts(db)

        if not accounts:
            print("No service accounts found.")
            return

        print(f"\n📋 LinkedIn Service Accounts ({len(accounts)} total):\n")
        print(f"{'ID':<38} {'Email':<25} {'Premium':<10} {'Active':<10} {'Last Used':<20} {'Requests Today'}")
        print("-" * 130)

        for account in accounts:
            last_used = account['last_used_at'].strftime('%Y-%m-%d %H:%M') if account['last_used_at'] else 'Never'
            print(
                f"{account['id']:<38} "
                f"{account['email']:<25} "
                f"{'Yes' if account['is_premium'] else 'No':<10} "
                f"{'Yes' if account['is_active'] else 'No':<10} "
                f"{last_used:<20} "
                f"{account['requests_count_today']}"
            )

    except Exception as e:
        print(f"❌ Failed to list accounts: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


def deactivate_account(account_id: str):
    """Deactivate a service account"""
    db = SessionLocal()
    try:
        ServiceAccountManager.deactivate_account(db, account_id)
        print(f"✅ Account {account_id} deactivated successfully!")

    except Exception as e:
        print(f"❌ Failed to deactivate account: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Manage LinkedIn service accounts for scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a basic account
  python scripts/add_service_account.py --email "scraper@example.com" --password "mypassword"

  # Add a premium account
  python scripts/add_service_account.py --email "premium@example.com" --password "pass" --premium

  # List all accounts
  python scripts/add_service_account.py --list

  # Deactivate an account
  python scripts/add_service_account.py --deactivate "account-uuid-here"
        """
    )

    parser.add_argument('--email', type=str, help='LinkedIn email address')
    parser.add_argument('--password', type=str, help='LinkedIn password')
    parser.add_argument('--premium', action='store_true', help='Mark as premium account')
    parser.add_argument('--list', action='store_true', help='List all service accounts')
    parser.add_argument('--deactivate', type=str, metavar='ACCOUNT_ID', help='Deactivate account by ID')

    args = parser.parse_args()

    # List accounts
    if args.list:
        list_accounts()
        return

    # Deactivate account
    if args.deactivate:
        deactivate_account(args.deactivate)
        return

    # Add account
    if args.email and args.password:
        add_account(args.email, args.password, args.premium)
        return

    # No valid action
    parser.print_help()
    sys.exit(1)


if __name__ == '__main__':
    main()
