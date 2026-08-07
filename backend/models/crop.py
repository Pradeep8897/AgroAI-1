from extensions import db
from models.orm_models import Crop


class CropModel:
    @staticmethod
    def save_recommendation(user_id, crop_name, N, P, K, ph, temperature, humidity, rainfall, prediction):
        try:
            crop = Crop(
                user_id=user_id,
                name=crop_name,
                N=int(N) if N is not None else None,
                P=int(P) if P is not None else None,
                K=int(K) if K is not None else None,
                ph=float(ph) if ph is not None else None,
                temperature=float(temperature) if temperature is not None else None,
                humidity=float(humidity) if humidity is not None else None,
                rainfall=float(rainfall) if rainfall is not None else None,
                prediction=prediction,
            )
            db.session.add(crop)
            db.session.commit()
        except Exception:
            db.session.rollback()

    @staticmethod
    def get_history_by_user(user_id):
        try:
            query = Crop.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            crops = query.order_by(Crop.created_at.desc()).all()
            return [
                {
                    "id": crop.id,
                    "user_id": crop.user_id,
                    "name": crop.name,
                    "N": crop.N,
                    "P": crop.P,
                    "K": crop.K,
                    "ph": float(crop.ph) if crop.ph is not None else None,
                    "temperature": float(crop.temperature) if crop.temperature is not None else None,
                    "humidity": float(crop.humidity) if crop.humidity is not None else None,
                    "rainfall": float(crop.rainfall) if crop.rainfall is not None else None,
                    "prediction": crop.prediction,
                    "created_at": crop.created_at.isoformat() if crop.created_at else None,
                }
                for crop in crops
            ]
        except Exception:
            return []
