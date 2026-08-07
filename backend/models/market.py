from models.orm_models import MarketPrice


class MarketModel:
    @staticmethod
    def get_prices_by_crop(crop_name):
        query = MarketPrice.query
        if crop_name:
            query = query.filter(MarketPrice.crop_name.ilike(f"%{crop_name}%"))
        prices = query.order_by(MarketPrice.id.asc()).all()
        return [
            {
                "id": price.id,
                "crop_name": price.crop_name,
                "market_name": price.market_name,
                "state": price.state,
                "current_price": float(price.current_price or 0.0),
                "predicted_price": float(price.predicted_price or 0.0),
                "date": price.date,
            }
            for price in prices
        ]

    @staticmethod
    def get_all_prices():
        return MarketModel.get_prices_by_crop(None)
