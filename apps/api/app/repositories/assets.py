from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset


class AssetsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_assets(self) -> list[Asset]:
        statement = select(Asset).order_by(Asset.hostname)
        return list(self.session.scalars(statement))

    def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        return asset

