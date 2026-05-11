"""Report service for handling user reports."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditAction, AuditTargetType
from app.models.chat import PersonaMessage
from app.models.persona import Persona
from app.models.report import Report, ReportStatus, ReportTargetType
from app.models.sharing import ShareLink
from app.models.storybook import StoryBook
from app.models.user import User
from app.schemas.report import CreateReportRequest, ReportResponse, AdminReportResponse
from app.utils.exceptions import ForbiddenException, NotFoundException, BadRequestException


class ReportService:
    """Service for handling user reports."""

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def create_report(
        db: Session,
        user_id: int,
        request_data: CreateReportRequest,
    ) -> ReportResponse:
        """Create a new report.

        Args:
            db: Database session
            user_id: ID of the reporting user
            request_data: Report creation request data

        Returns:
            ReportResponse with created report data
        """
        # Validate that the target exists based on target_type
        ReportService._validate_target_exists(db, request_data.target_type, request_data.target_id)

        report = Report(
            reporter_user_id=user_id,
            target_type=request_data.target_type,
            target_id=request_data.target_id,
            reason_type=request_data.reason_type,
            reason_detail=request_data.reason_detail,
            status=ReportStatus.PENDING,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Create audit log
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.REPORT_CREATED,
                actor_user_id=user_id,
                target_type=AuditTargetType.REPORT,
                target_id=report.id,
                description=f"Report created for {request_data.target_type.value}",
                metadata={
                    "target_type": request_data.target_type.value,
                    "target_id": request_data.target_id,
                    "reason_type": request_data.reason_type.value,
                },
            )
        except Exception:
            pass

        return ReportResponse.model_validate(report)

    @staticmethod
    def get_user_reports(
        db: Session,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """Get reports created by the user.

        Args:
            db: Database session
            user_id: ID of the user
            page: Page number (1-indexed)
            size: Page size

        Returns:
            Dictionary with total count and list of reports
        """
        # Get total count
        count_query = select(Report).where(Report.reporter_user_id == user_id)
        total = len(db.execute(count_query).scalars().all())

        # Get paginated results
        reports = (
            db.execute(
                select(Report)
                .where(Report.reporter_user_id == user_id)
                .order_by(Report.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
            .scalars()
            .all()
        )

        return {
            "total": total,
            "items": [ReportResponse.model_validate(r) for r in reports],
        }

    @staticmethod
    def get_user_report(
        db: Session,
        user_id: int,
        report_id: int,
    ) -> ReportResponse:
        """Get a specific report created by the user.

        Args:
            db: Database session
            user_id: ID of the user
            report_id: ID of the report

        Returns:
            ReportResponse

        Raises:
            NotFoundException: If report doesn't exist
            ForbiddenException: If user is not the report creator
        """
        report = db.get(Report, report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        if report.reporter_user_id != user_id:
            raise ForbiddenException("You can only view your own reports")

        return ReportResponse.model_validate(report)

    @staticmethod
    def get_admin_reports(
        db: Session,
        status: Optional[ReportStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """Get all reports (admin only).

        Args:
            db: Database session
            status: Optional status filter
            page: Page number (1-indexed)
            size: Page size

        Returns:
            Dictionary with total count and list of reports
        """
        query = select(Report)
        if status:
            query = query.where(Report.status == status)

        # Get total count
        total_query = select(Report)
        if status:
            total_query = total_query.where(Report.status == status)
        total = len(db.execute(total_query).scalars().all())

        # Get paginated results
        reports = (
            db.execute(
                query.order_by(Report.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
            .scalars()
            .all()
        )

        # Load related users for each report
        result = []
        for report in reports:
            reporter = db.get(User, report.reporter_user_id)
            reviewer = db.get(User, report.reviewed_by) if report.reviewed_by else None
            result.append(AdminReportResponse(
                id=report.id,
                reporter_user_id=report.reporter_user_id,
                reporter_email=reporter.email if reporter else None,
                reporter_nickname=reporter.nickname if reporter else None,
                target_type=report.target_type,
                target_id=report.target_id,
                reason_type=report.reason_type,
                reason_detail=report.reason_detail,
                status=report.status,
                reviewed_by=report.reviewed_by,
                reviewed_by_email=reviewer.email if reviewer else None,
                reviewed_at=report.reviewed_at,
                admin_note=report.admin_note,
                created_at=report.created_at,
                updated_at=report.updated_at,
            ))

        return {
            "total": total,
            "items": result,
        }

    @staticmethod
    def get_admin_report(
        db: Session,
        report_id: int,
    ) -> AdminReportResponse:
        """Get a specific report (admin only).

        Args:
            db: Database session
            report_id: ID of the report

        Returns:
            AdminReportResponse

        Raises:
            NotFoundException: If report doesn't exist
        """
        report = db.get(Report, report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        reporter = db.get(User, report.reporter_user_id)
        reviewer = db.get(User, report.reviewed_by) if report.reviewed_by else None

        return AdminReportResponse(
            id=report.id,
            reporter_user_id=report.reporter_user_id,
            reporter_email=reporter.email if reporter else None,
            reporter_nickname=reporter.nickname if reporter else None,
            target_type=report.target_type,
            target_id=report.target_id,
            reason_type=report.reason_type,
            reason_detail=report.reason_detail,
            status=report.status,
            reviewed_by=report.reviewed_by,
            reviewed_by_email=reviewer.email if reviewer else None,
            reviewed_at=report.reviewed_at,
            admin_note=report.admin_note,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )

    @staticmethod
    def update_report_reviewing(
        db: Session,
        admin_user_id: int,
        report_id: int,
        admin_note: Optional[str] = None,
    ) -> AdminReportResponse:
        """Mark report as under review (admin only).

        Args:
            db: Database session
            admin_user_id: ID of the admin user
            report_id: ID of the report
            admin_note: Optional admin note

        Returns:
            AdminReportResponse
        """
        report = db.get(Report, report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        if report.status == ReportStatus.REVIEWING:
            raise BadRequestException("Report is already under review")

        report.status = ReportStatus.REVIEWING
        report.reviewed_by = admin_user_id
        report.reviewed_at = ReportService._now()
        if admin_note:
            report.admin_note = admin_note
        db.commit()
        db.refresh(report)

        # Create audit log
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.REPORT_REVIEWING,
                actor_user_id=admin_user_id,
                target_type=AuditTargetType.REPORT,
                target_id=report.id,
                description="Report marked as under review",
                metadata={"report_id": report.id},
            )
        except Exception:
            pass

        return ReportService.get_admin_report(db, report_id)

    @staticmethod
    def resolve_report(
        db: Session,
        admin_user_id: int,
        report_id: int,
        admin_note: Optional[str] = None,
    ) -> AdminReportResponse:
        """Resolve report without taking action (admin only).

        Args:
            db: Database session
            admin_user_id: ID of the admin user
            report_id: ID of the report
            admin_note: Optional admin note

        Returns:
            AdminReportResponse
        """
        report = db.get(Report, report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        report.status = ReportStatus.RESOLVED
        report.reviewed_by = admin_user_id
        report.reviewed_at = ReportService._now()
        if admin_note:
            report.admin_note = admin_note
        db.commit()
        db.refresh(report)

        # Create audit log
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.REPORT_RESOLVED,
                actor_user_id=admin_user_id,
                target_type=AuditTargetType.REPORT,
                target_id=report.id,
                description="Report resolved",
                metadata={"report_id": report.id},
            )
        except Exception:
            pass

        return ReportService.get_admin_report(db, report_id)

    @staticmethod
    def reject_report(
        db: Session,
        admin_user_id: int,
        report_id: int,
        admin_note: Optional[str] = None,
    ) -> AdminReportResponse:
        """Reject report (admin only).

        Args:
            db: Database session
            admin_user_id: ID of the admin user
            report_id: ID of the report
            admin_note: Optional admin note

        Returns:
            AdminReportResponse
        """
        report = db.get(Report, report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        report.status = ReportStatus.REJECTED
        report.reviewed_by = admin_user_id
        report.reviewed_at = ReportService._now()
        if admin_note:
            report.admin_note = admin_note
        db.commit()
        db.refresh(report)

        # Create audit log
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.REPORT_REJECTED,
                actor_user_id=admin_user_id,
                target_type=AuditTargetType.REPORT,
                target_id=report.id,
                description="Report rejected",
                metadata={"report_id": report.id},
            )
        except Exception:
            pass

        return ReportService.get_admin_report(db, report_id)

    @staticmethod
    def take_action_on_report(
        db: Session,
        admin_user_id: int,
        report_id: int,
        admin_note: Optional[str] = None,
    ) -> AdminReportResponse:
        """Take action on report (admin only).

        This marks the report as ACTION_TAKEN and applies appropriate restrictions
        based on the target type.

        Args:
            db: Database session
            admin_user_id: ID of the admin user
            report_id: ID of the report
            admin_note: Optional admin note

        Returns:
            AdminReportResponse
        """
        report = db.get(Report, report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        # Apply action based on target_type
        ReportService._apply_report_action(db, report)

        report.status = ReportStatus.ACTION_TAKEN
        report.reviewed_by = admin_user_id
        report.reviewed_at = ReportService._now()
        if admin_note:
            report.admin_note = admin_note
        db.commit()
        db.refresh(report)

        # Create audit log
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.REPORT_ACTION_TAKEN,
                actor_user_id=admin_user_id,
                target_type=AuditTargetType.REPORT,
                target_id=report.id,
                description=f"Action taken on report - disabled {report.target_type.value}",
                metadata={
                    "report_id": report.id,
                    "target_type": report.target_type.value,
                    "target_id": report.target_id,
                },
            )
        except Exception:
            pass

        return ReportService.get_admin_report(db, report_id)

    @staticmethod
    def _apply_report_action(db: Session, report: Report) -> None:
        """Apply appropriate action based on report target type.

        Args:
            db: Database session
            report: The report object
        """
        now = ReportService._now()

        if report.target_type == ReportTargetType.PERSONA:
            persona = db.get(Persona, report.target_id)
            if persona:
                persona.disabled_at = now
                persona.disabled_reason = f"Reported: {report.reason_type.value}"
                db.commit()

        elif report.target_type == ReportTargetType.STORYBOOK:
            storybook = db.get(StoryBook, report.target_id)
            if storybook:
                storybook.disabled_at = now
                db.commit()

        elif report.target_type == ReportTargetType.SHARE_LINK:
            share_link = db.get(ShareLink, report.target_id)
            if share_link:
                share_link.disabled_at = now
                share_link.is_active = False
                db.commit()

        elif report.target_type == ReportTargetType.PERSONA_MESSAGE:
            message = db.get(PersonaMessage, report.target_id)
            if message:
                message.hidden_at = now
                message.hidden_reason = f"Reported: {report.reason_type.value}"
                db.commit()

    @staticmethod
    def _validate_target_exists(db: Session, target_type: ReportTargetType, target_id: int) -> None:
        """Validate that the target exists.

        Args:
            db: Database session
            target_type: Type of target
            target_id: ID of target

        Raises:
            NotFoundException: If target doesn't exist
        """
        from app.models.chat import PersonaChat
        from app.models.target import Target

        if target_type == ReportTargetType.PERSONA:
            if not db.get(Persona, target_id):
                raise NotFoundException(f"Persona {target_id} not found")
        elif target_type == ReportTargetType.PERSONA_CHAT:
            if not db.get(PersonaChat, target_id):
                raise NotFoundException(f"PersonaChat {target_id} not found")
        elif target_type == ReportTargetType.PERSONA_MESSAGE:
            if not db.get(PersonaMessage, target_id):
                raise NotFoundException(f"PersonaMessage {target_id} not found")
        elif target_type == ReportTargetType.STORYBOOK:
            if not db.get(StoryBook, target_id):
                raise NotFoundException(f"StoryBook {target_id} not found")
        elif target_type == ReportTargetType.SHARE_LINK:
            if not db.get(ShareLink, target_id):
                raise NotFoundException(f"ShareLink {target_id} not found")
        elif target_type == ReportTargetType.TARGET:
            if not db.get(Target, target_id):
                raise NotFoundException(f"Target {target_id} not found")
        elif target_type == ReportTargetType.USER:
            if not db.get(User, target_id):
                raise NotFoundException(f"User {target_id} not found")


# Create singleton instance
report_service = ReportService()


