from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import hashlib

from ..models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, token_str: str, expires_at: datetime, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> RefreshToken:
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(rt)
        self.db.commit()
        self.db.refresh(rt)
        return rt

    def get_by_hash(self, token_str: str) -> Optional[RefreshToken]:
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        return self.db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
        self.db.commit()

    def revoke_all_for_user(self, user_id: int) -> int:
        tokens = self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False).all()
        count = 0
        for t in tokens:
            t.revoked = True
            count += 1
        self.db.commit()
        return count

    def mark_replaced(self, old_token: RefreshToken, new_token: RefreshToken) -> None:
        old_token.revoked = True
        old_token.replaced_by_id = new_token.id
        self.db.commit()
