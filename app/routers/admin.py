from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.citizen_report import CitizenReport, ReportStatus
from app.models.report_review_log import ReportReviewLog
from app.models.audit_log import AuditLog
from app.deps import get_current_user, require_roles, get_current_admin, get_current_investigator_or_admin
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/admin", tags=["Admin & Governance"])

class ReportReviewRequest(BaseModel):
    action: str  # APPROVE, REJECT, ESCALATE, UNDER_REVIEW
    notes: Optional[str] = None

class RoleUpdateRequest(BaseModel):
    role: str

@router.get("/reports")
def list_citizen_reports_for_admin(
    status_filter: Optional[ReportStatus] = None,
    current_user: User = Depends(get_current_investigator_or_admin),
    db: Session = Depends(get_db)
):
    """List all citizen reports for administrative review (Investigators & Admins)."""
    query = db.query(CitizenReport)
    if status_filter:
        query = query.filter(CitizenReport.status == status_filter)
    reports = query.order_by(CitizenReport.created_at.desc()).all()
    return {
        "success": True,
        "count": len(reports),
        "reports": [r.to_dict() for r in reports]
    }

@router.post("/reports/{report_id}/review")
def review_citizen_report(
    report_id: str,
    payload: ReportReviewRequest,
    request: Request,
    current_user: User = Depends(get_current_investigator_or_admin),
    db: Session = Depends(get_db)
):
    """Review a citizen report: Approve, Reject, or Escalate."""
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": "Citizen report not found."}
        )

    action_upper = payload.action.upper()
    old_status = report.status.value if isinstance(report.status, ReportStatus) else str(report.status)

    if action_upper == "APPROVE":
        new_status = ReportStatus.APPROVED
    elif action_upper == "REJECT":
        new_status = ReportStatus.REJECTED
    elif action_upper == "ESCALATE":
        new_status = ReportStatus.ESCALATED
    elif action_upper == "UNDER_REVIEW":
        new_status = ReportStatus.UNDER_REVIEW
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ACTION", "message": "Action must be one of: APPROVE, REJECT, ESCALATE, UNDER_REVIEW"}
        )

    report.status = new_status
    db.commit()
    db.refresh(report)

    # Log review transition
    review_log = ReportReviewLog(
        report_id=report.id,
        reviewed_by_id=current_user.id,
        old_status=old_status,
        new_status=new_status.value,
        action=action_upper,
        notes=payload.notes
    )
    db.add(review_log)
    db.commit()

    log_audit_event(
        db=db,
        action=f"REPORT_{action_upper}",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="CITIZEN_REPORT",
        resource_id=report.id,
        details=f"Report {report.id} transitioned from {old_status} to {new_status.value}. Notes: {payload.notes or 'None'}",
        ip_address=request.client.host if request.client else None
    )

    return {
        "success": True,
        "message": f"Report successfully updated to {new_status.value}.",
        "report": report.to_dict()
    }

@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List system users (Admins only)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "success": True,
        "count": len(users),
        "users": [u.to_dict() for u in users]
    }

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update role of a user (Admins only)."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Target user not found."}
        )

    old_role = target_user.role.value if isinstance(target_user.role, UserRole) else str(target_user.role)
    try:
        new_role_enum = UserRole(payload.role.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ROLE", "message": "Role must be one of: CITIZEN, INVESTIGATOR, ADMIN"}
        )
    target_user.role = new_role_enum
    db.commit()
    db.refresh(target_user)

    log_audit_event(
        db=db,
        action="USER_ROLE_CHANGE",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="USER",
        resource_id=target_user.id,
        details=f"Role of user {target_user.username} changed from {old_role} to {payload.role.value}",
        ip_address=request.client.host if request.client else None
    )

    return {
        "success": True,
        "message": f"User role updated to {payload.role.value}.",
        "user": target_user.to_dict()
    }

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """View system audit logs (Admins only)."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return {
        "success": True,
        "count": len(logs),
        "audit_logs": [l.to_dict() for l in logs]
    }
