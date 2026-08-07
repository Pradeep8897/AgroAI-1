from extensions import db
from models.orm_models import Disease, DiseaseReport


class DiseaseModel:
    @staticmethod
    def get_disease_by_name(name):
        if not name:
            return None
        return Disease.query.filter(Disease.name.ilike(name)).first()

    @staticmethod
    def save_report(user_id, crop_name, disease_name, severity, image_path):
        try:
            report = DiseaseReport(
                user_id=user_id,
                crop_name=crop_name,
                disease_name=disease_name,
                severity=severity,
                image_path=image_path,
                status='pending',
            )
            db.session.add(report)
            db.session.commit()
        except Exception:
            db.session.rollback()

    @staticmethod
    def get_reports_by_user(user_id):
        query = DiseaseReport.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        reports = query.order_by(DiseaseReport.created_at.desc()).all()
        return [
            {
                "id": report.id,
                "user_id": report.user_id,
                "crop_name": report.crop_name,
                "disease_name": report.disease_name,
                "severity": report.severity,
                "image_path": report.image_path,
                "status": report.status,
                "created_at": report.created_at.isoformat() if report.created_at else None,
            }
            for report in reports
        ]
