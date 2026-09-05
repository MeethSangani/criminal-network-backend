from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.citizen_report import CitizenReport, ReportStatus
from app.deps import get_current_user
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/citizen-reports", tags=["Citizen Reporting"])

class CitizenReportCreateRequest(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    event_date: Optional[str] = None
    person_details: Optional[str] = None
    vehicle_details: Optional[str] = None
    attachment_metadata: Optional[str] = None

@router.post("", status_code=status.HTTP_201_CREATED)
def submit_citizen_report(
    payload: CitizenReportCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a suspicious activity report. Initially assigned status PENDING."""
    report = CitizenReport(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        event_date=payload.event_date,
        person_details=payload.person_details,
        vehicle_details=payload.vehicle_details,
        attachment_metadata=payload.attachment_metadata,
        status=ReportStatus.PENDING
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    log_audit_event(
        db=db,
        action="CITIZEN_REPORT_SUBMIT",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="CITIZEN_REPORT",
        resource_id=report.id,
        details=f"Report submitted: {report.title}",
        ip_address=request.client.host if request.client else None
    )

    return {
        "success": True,
        "message": "Suspicious activity report submitted successfully. Currently pending review.",
        "report": report.to_dict()
    }

@router.get("/my-reports")
def get_my_citizen_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reports submitted by current authenticated user (Privacy Enforcement)."""
    reports = db.query(CitizenReport).filter(CitizenReport.user_id == current_user.id).order_by(CitizenReport.created_at.desc()).all()
    return {
        "success": True,
        "count": len(reports),
        "reports": [r.to_dict() for r in reports]
    }

@router.get("/{report_id}")
def get_citizen_report_by_id(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific citizen report. Citizens can only view their own reports."""
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": "Report record not found."}
        )

    # Privacy Enforcement: Citizen can only view own reports
    user_role = current_user.role if isinstance(current_user.role, UserRole) else UserRole(str(current_user.role))
    if user_role == UserRole.CITIZEN and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PRIVACY_RESTRICTION", "message": "You can only view your own submitted reports."}
        )

    return {
        "success": True,
        "report": report.to_dict()
    }
