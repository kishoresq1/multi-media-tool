from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LinkedInOAuthToken


class LinkedInTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active(self) -> LinkedInOAuthToken | None:
        result = await self.session.execute(
            select(LinkedInOAuthToken).order_by(LinkedInOAuthToken.updated_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        member_sub: str,
        member_urn: str,
        display_name: str,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime | None,
        scopes: str,
    ) -> LinkedInOAuthToken:
        existing = await self.get_active()
        now = datetime.now(timezone.utc)
        if existing:
            existing.member_sub = member_sub
            existing.member_urn = member_urn
            existing.display_name = display_name
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.expires_at = expires_at
            existing.scopes = scopes
            existing.updated_at = now
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        row = LinkedInOAuthToken(
            member_sub=member_sub,
            member_urn=member_urn,
            display_name=display_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=scopes,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def delete_all(self) -> None:
        result = await self.session.execute(select(LinkedInOAuthToken))
        for row in result.scalars().all():
            await self.session.delete(row)
        await self.session.commit()
