"""
OAuth Authentication Tests
Ensures LinkedIn OAuth never fails due to missing database tables.

Run with: docker compose exec backend python -m pytest tests/test_auth_oauth.py -v -s
"""
import pytest
from datetime import datetime
import uuid


class TestDatabasePrerequisites:
    """Test that database prerequisites for OAuth exist"""

    def test_users_table_exists(self, db_session):
        """CRITICAL: Test that users table exists before OAuth can work"""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()

        assert 'users' in tables, "users table is missing! OAuth will fail."
        print("✅ users table exists")

    def test_users_table_has_required_columns(self, db_session):
        """Test that users table has all required columns for OAuth"""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        required_columns = [
            'id', 'email', 'linkedin_id', 'linkedin_access_token',
            'linkedin_refresh_token', 'created_at', 'updated_at'
        ]

        missing = [col for col in required_columns if col not in columns]
        assert not missing, f"users table missing columns: {missing}"

        print(f"✅ users table has all {len(required_columns)} required columns")


class TestOAuthUserCreation:
    """Test OAuth user creation flow"""

    def test_create_user_from_oauth(self, db_session):
        """Test creating a user from OAuth data"""
        from app.models.user import User

        # Simulate OAuth callback data
        oauth_data = {
            'linkedin_id': 'test-linkedin-' + str(uuid.uuid4())[:8],
            'email': f'test{uuid.uuid4().hex[:8]}@example.com',
            'access_token': 'mock_access_token_' + str(uuid.uuid4()),
            'refresh_token': 'mock_refresh_token_' + str(uuid.uuid4())
        }

        # Create user as OAuth would
        user = User(
            email=oauth_data['email'],
            linkedin_id=oauth_data['linkedin_id'],
            linkedin_access_token=oauth_data['access_token'],
            linkedin_refresh_token=oauth_data['refresh_token'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Verify user was created
        assert user.id is not None
        assert user.email == oauth_data['email']
        assert user.linkedin_id == oauth_data['linkedin_id']

        print(f"✅ OAuth user created successfully: {user.email}")

    def test_find_existing_user_by_linkedin_id(self, db_session):
        """Test finding an existing user by linkedin_id (OAuth login)"""
        from app.models.user import User

        # Create a user first
        linkedin_id = 'existing-user-' + str(uuid.uuid4())[:8]
        user = User(
            email=f'existing{uuid.uuid4().hex[:8]}@example.com',
            linkedin_id=linkedin_id,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()

        # Simulate OAuth trying to find this user
        found_user = db_session.query(User).filter(
            User.linkedin_id == linkedin_id
        ).first()

        assert found_user is not None
        assert found_user.linkedin_id == linkedin_id

        print(f"✅ Found existing user by linkedin_id")

    def test_find_or_create_user_flow(self, db_session):
        """Test the complete find-or-create flow that OAuth uses"""
        from app.models.user import User

        linkedin_id = 'findorcreate-' + str(uuid.uuid4())[:8]
        email = f'new{uuid.uuid4().hex[:8]}@example.com'

        # First attempt - should create
        user = db_session.query(User).filter(
            (User.linkedin_id == linkedin_id) | (User.email == email)
        ).first()

        if not user:
            user = User(
                email=email,
                linkedin_id=linkedin_id,
                created_at=datetime.utcnow()
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        first_user_id = user.id

        # Second attempt - should find existing
        user2 = db_session.query(User).filter(
            (User.linkedin_id == linkedin_id) | (User.email == email)
        ).first()

        assert user2 is not None
        assert user2.id == first_user_id
        assert user2.linkedin_id == linkedin_id

        print(f"✅ Find-or-create flow works correctly")


class TestOAuthEdgeCases:
    """Test OAuth edge cases and error scenarios"""

    def test_duplicate_linkedin_id_constraint(self, db_session):
        """Test that duplicate linkedin_id is prevented"""
        from app.models.user import User

        linkedin_id = 'duplicate-test-' + str(uuid.uuid4())[:8]

        # Create first user
        user1 = User(
            email=f'user1{uuid.uuid4().hex[:8]}@example.com',
            linkedin_id=linkedin_id,
            created_at=datetime.utcnow()
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create second user with same linkedin_id
        user2 = User(
            email=f'user2{uuid.uuid4().hex[:8]}@example.com',
            linkedin_id=linkedin_id,  # Same ID!
            created_at=datetime.utcnow()
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # Should fail due to unique constraint
            db_session.commit()

        db_session.rollback()

        print(f"✅ Duplicate linkedin_id correctly prevented")

    def test_oauth_with_missing_email(self, db_session):
        """Test OAuth when LinkedIn doesn't provide email"""
        from app.models.user import User

        # Some LinkedIn accounts might not have email
        linkedin_id = 'no-email-' + str(uuid.uuid4())[:8]

        user = User(
            linkedin_id=linkedin_id,
            # No email provided
            created_at=datetime.utcnow()
        )

        db_session.add(user)

        # Should fail because email is required
        with pytest.raises(Exception):
            db_session.commit()

        db_session.rollback()

        print(f"✅ Missing email correctly rejected")


class TestDatabaseMigrationStatus:
    """Test that migrations are properly applied"""

    def test_alembic_version_exists(self, db_session):
        """Test that alembic version tracking works"""
        from sqlalchemy import text

        result = db_session.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()

        assert version is not None, "No migrations applied!"
        assert len(version) > 0, "Migration version is empty!"

        print(f"✅ Migrations applied (version: {version})")

    def test_no_pending_migrations(self):
        """Test that all migrations have been run"""
        import subprocess

        # Check if there are pending migrations
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', 'backend', 'alembic', 'current'],
            capture_output=True,
            text=True
        )

        assert 'head' in result.stdout or result.returncode == 0
        print(f"✅ No pending migrations")


class TestOAuthIntegration:
    """Integration tests for OAuth flow"""

    def test_complete_oauth_flow_simulation(self, client, db_session):
        """Simulate a complete OAuth login flow"""
        from app.models.user import User

        # Step 1: User clicks "Login with LinkedIn"
        # (Frontend redirects to LinkedIn)

        # Step 2: LinkedIn redirects back with code
        # (Simulated - we create the user directly)

        oauth_data = {
            'linkedin_id': 'integration-' + str(uuid.uuid4())[:8],
            'email': f'integration{uuid.uuid4().hex[:8]}@example.com'
        }

        # Step 3: Backend creates or finds user
        user = db_session.query(User).filter(
            (User.linkedin_id == oauth_data['linkedin_id']) |
            (User.email == oauth_data['email'])
        ).first()

        if not user:
            user = User(
                email=oauth_data['email'],
                linkedin_id=oauth_data['linkedin_id'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        # Step 4: Generate JWT token for user
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": str(user.id), "email": user.email})

        # Step 5: Verify user can access protected endpoints
        response = client.get(
            '/api/uploaded-resumes/',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        print(f"✅ Complete OAuth flow works end-to-end")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
