#!/usr/bin/env python3
"""
Fix script to create LinkedIn profiles for existing users who don't have one.
This fixes the issue where users registered before the auto-profile-creation fix.

Run with: docker compose exec backend python scripts/fix_missing_profiles.py
"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import LinkedInProfile


def fix_missing_profiles():
    """Create LinkedIn profiles for users who don't have one"""
    db = SessionLocal()

    try:
        # Get all users
        users = db.query(User).all()
        print(f"Found {len(users)} users in database")

        fixed_count = 0
        already_have_profile = 0

        for user in users:
            # Check if user has a profile
            profile = db.query(LinkedInProfile).filter(
                LinkedInProfile.user_id == user.id
            ).first()

            if profile is None:
                # Create empty profile
                print(f"Creating profile for user: {user.email}")

                empty_profile = LinkedInProfile(
                    user_id=user.id,
                    headline="",
                    summary="",
                    raw_data={"name": user.email.split('@')[0]},
                    experiences=[],
                    education=[],
                    skills=[],
                    certifications=[]
                )
                db.add(empty_profile)
                fixed_count += 1
            else:
                already_have_profile += 1

        # Commit all changes
        db.commit()

        print(f"\n✅ Profile creation complete:")
        print(f"   - Created profiles: {fixed_count}")
        print(f"   - Already had profiles: {already_have_profile}")
        print(f"   - Total users: {len(users)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    fix_missing_profiles()
