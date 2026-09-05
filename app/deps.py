from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import decode_access_token, hash_password
from app.services.audit_service import log_audit_event

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT access token from Authorization Bearer header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication token required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User account no longer exists."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INACTIVE_USER", "message": "User account is disabled."},
        )
    
    return user

def require_roles(allowed_roles: List[UserRole]):
    """Role-Based Access Control (RBAC) Dependency Factory."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role).replace("UserRole.", "")
        allowed_vals = [r.value for r in allowed_roles]
        if user_role_val not in allowed_vals:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": f"Operation requires one of the following roles: {allowed_vals}. Your role: {user_role_val}"
                }
            )
        return current_user
    return role_checker

# Helper dependencies
get_current_admin = require_roles([UserRole.ADMIN])
get_current_investigator_or_admin = require_roles([UserRole.INVESTIGATOR, UserRole.ADMIN])
get_current_active_user = require_roles([UserRole.CITIZEN, UserRole.INVESTIGATOR, UserRole.ADMIN])

def seed_demo_users_if_needed(db: Session):
    """Seed initial demo users if the users table is completely empty."""
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            demo_users = [
                User(
                    username="admin",
                    email="admin@sih.gov.in",
                    full_name="System Administrator",
                    hashed_password=hash_password("admin123"),
                    role=UserRole.ADMIN,
                    is_active=True
                ),
                User(
                    username="investigator",
                    email="investigator@sih.gov.in",
                    full_name="Senior Intelligence Officer",
                    hashed_password=hash_password("investigator123"),
                    role=UserRole.INVESTIGATOR,
                    is_active=True
                ),
                User(
                    username="citizen",
                    email="citizen@sih.gov.in",
                    full_name="Rajesh Citizen",
                    hashed_password=hash_password("citizen123"),
                    role=UserRole.CITIZEN,
                    is_active=True
                )
            ]
            db.add_all(demo_users)
            db.commit()
            for u in demo_users:
                log_audit_event(
                    db=db,
                    action="SYSTEM_INIT_USER",
                    user_id=u.id,
                    username=u.username,
                    details=f"Demo account created with role {u.role.value}"
                )
    except Exception as e:
        db.rollback()
        print(f"Demo user seeding skipped or failed: {e}")
