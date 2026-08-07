import random
from datetime import datetime

from models.orm_models import Notification

class NotificationModel:
    @staticmethod
    def get_active_alerts(user_id=None):
        # We can return dynamic simulated location-based weather and pest alerts
        # to show in the farmer dashboard
        alerts = [
            {
                "id": 1,
                "title": "Severe Heatwave Alert",
                "message": "Temperatures are expected to exceed 42°C in your region over the next 3 days. Irrigate crops in early morning/late evening.",
                "severity": "critical",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": "weather"
            },
            {
                "id": 2,
                "title": "Aphid Pest Advisory",
                "message": "Increased aphid activity reported in nearby potato farms. Check leaves regularly and apply organic neem oil or recommended insecticides.",
                "severity": "warning",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": "pest"
            },
            {
                "id": 3,
                "title": "Mandi Price Hike: Rice",
                "message": "Basmati rice rates spiked by 8% in Karnal Mandi. Good opportunity to sell stored stocks.",
                "severity": "info",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": "market"
            }
        ]
        return alerts
