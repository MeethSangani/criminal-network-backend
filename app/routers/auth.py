from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.services.audit_service import log_audit_event
from app.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "CITIZEN"

class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USERNAME_TAKEN", "message": "Username is already registered."}
        )
    
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMAIL_TAKEN", "message": "Email is already registered."}
        )
    
    role_str = (payload.role or "CITIZEN").upper()
    try:
        user_role_enum = UserRole(role_str)
    except ValueError:
        user_role_enum = UserRole.CITIZEN

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=user_role_enum,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="USER_REGISTER",
        user_id=user.id,
        username=user.username,
        resource_type="USER",
        resource_id=user.id,
        details=f"User registered with role {user.role}",
        ip_address=request.client.host if request.client else None
    )

    token = create_access_token({"sub": user.id, "role": user.role.value if isinstance(user.role, UserRole) else str(user.role)})

    return {
        "success": True,
        "message": "User account created successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.post("/login")
def login_user(payload: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    user = db.query(User).filter(
        (User.username == payload.username_or_email) | (User.email == payload.username_or_email)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username/email or password."}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INACTIVE_USER", "message": "Account is disabled."}
        )

    token = create_access_token({"sub": user.id, "role": user.role.value if isinstance(user.role, UserRole) else str(user.role)})

    log_audit_event(
        db=db,
        action="USER_LOGIN",
        user_id=user.id,
        username=user.username,
        resource_type="USER",
        resource_id=user.id,
        details=f"User logged in with role {user.role}",
        ip_address=request.client.host if request.client else None
    )

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch profile of current authenticated user."""
    return {
        "success": True,
        "user": current_user.to_dict()
    }

@router.post("/logout")
def logout_user(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout current user and log audit event."""
    log_audit_event(
        db=db,
        action="USER_LOGOUT",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="USER",
        resource_id=current_user.id,
        ip_address=request.client.host if request.client else None
    )
    return {
        "success": True,
        "message": "Successfully logged out."
    }
