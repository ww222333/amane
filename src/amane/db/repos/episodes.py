"""剧集分集仓储: 写入合并与按剧列出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import col, select

from ...crawlers.models import EpisodeInfo
from ...utils.text import normalize_long_text
from ..models import Episode
from ..repo_types import _utcnow
from .base import RepositoryMixinBase

if TYPE_CHECKING:
    from collections.abc import Sequence


class EpisodesRepoMixin(RepositoryMixinBase):
    async def list_episodes(self, metadata_id: int) -> list[Episode]:
        async with self._session() as session:
            stmt = (
                select(Episode)
                .where(Episode.metadata_id == metadata_id)
                .order_by(col(Episode.season), col(Episode.episode))
            )
            result = await session.exec(stmt)
            return list(result.all())

    async def get_episode(self, episode_id: int) -> Episode | None:
        async with self._session() as session:
            return await session.get(Episode, episode_id)

    async def find_episode(
        self, metadata_id: int, *, season: int, episode: int
    ) -> Episode | None:
        async with self._session() as session:
            stmt = select(Episode).where(
                Episode.metadata_id == metadata_id,
                Episode.season == season,
                Episode.episode == episode,
            )
            result = await session.exec(stmt)
            return result.first()

    async def sync_episodes(
        self,
        metadata_id: int,
        episodes: Sequence[EpisodeInfo],
        *,
        episode_count: int | None = None,
        overwrite: bool = False,
    ) -> list[Episode]:
        """合并写入分集行.

        - 传入的 ``episodes`` 按 (season, episode) upsert.
        - ``overwrite=False`` (刮削默认): 非空 title/plot 只填补空位.
        - ``overwrite=True`` (用户选用某源): 用传入非空值覆盖已有 title/plot;
          传入显式空串时清空对应字段.
        - 若给出 ``episode_count`` 且大于已有最大集号, 补齐 1..N (season=1) 的空标题行.
        - 不删除站点未再返回的行 (本地文件可能已绑定).
        """
        async with self._session() as session:
            stmt = select(Episode).where(Episode.metadata_id == metadata_id)
            result = await session.exec(stmt)
            existing = {(row.season, row.episode): row for row in result.all()}

            for info in episodes:
                key = (info.season, info.episode)
                row = existing.get(key)
                title = (info.title or "").strip() or None
                plot = normalize_long_text(info.plot)
                if row is None:
                    row = Episode(
                        metadata_id=metadata_id,
                        season=info.season,
                        episode=info.episode,
                        title=title,
                        plot=plot,
                    )
                    session.add(row)
                    existing[key] = row
                elif overwrite:
                    changed = False
                    # 覆盖模式: 源给了标题/简介就写入; 源显式缺省 (None) 不清空已有值.
                    if info.title is not None:
                        new_title = (info.title or "").strip() or None
                        if row.title != new_title:
                            row.title = new_title
                            changed = True
                    if info.plot is not None:
                        new_plot = normalize_long_text(info.plot)
                        if row.plot != new_plot:
                            row.plot = new_plot
                            changed = True
                    if changed:
                        row.updated_at = _utcnow()
                        session.add(row)
                else:
                    changed = False
                    if title and not (row.title or "").strip():
                        row.title = title
                        changed = True
                    if plot and not (row.plot or "").strip():
                        row.plot = plot
                        changed = True
                    if changed:
                        row.updated_at = _utcnow()
                        session.add(row)

            max_ep = max((ep for _, ep in existing), default=0)
            target = max(episode_count or 0, max_ep)
            for n in range(1, target + 1):
                key = (1, n)
                if key in existing:
                    continue
                row = Episode(metadata_id=metadata_id, season=1, episode=n)
                session.add(row)
                existing[key] = row

            await session.commit()
            for row in existing.values():
                await session.refresh(row)
            return sorted(existing.values(), key=lambda e: (e.season, e.episode))

    async def apply_episodes_from_raw_source(
        self,
        metadata_id: int,
        source: str,
    ) -> list[Episode]:
        """从 ``Metadata.raw[source]`` 取出分集并覆盖写入; 同时更新 ``episode_count``.

        ``source`` 必须是 raw 中已有键. 该站无 episodes / episode_count 时抛 ValueError.
        """
        from ..models import Metadata

        async with self._session() as session:
            meta = await session.get(Metadata, metadata_id)
            if meta is None:
                msg = f"metadata {metadata_id} not found"
                raise ValueError(msg)
            raw = meta.raw or {}
            payload = raw.get(source)
            if not isinstance(payload, dict):
                msg = f"source {source!r} not in raw"
                raise ValueError(msg)

            episodes: list[EpisodeInfo] = []
            raw_eps = payload.get("episodes")
            if isinstance(raw_eps, list):
                for item in raw_eps:
                    if not isinstance(item, dict):
                        continue
                    try:
                        episodes.append(EpisodeInfo.model_validate(item))
                    except Exception:
                        continue

            ep_count: int | None = None
            raw_count = payload.get("episode_count")
            if isinstance(raw_count, int) and raw_count >= 1:
                ep_count = raw_count
            elif isinstance(raw_count, str) and raw_count.strip().isdigit():
                n = int(raw_count.strip())
                ep_count = n if n >= 1 else None

            if not episodes and ep_count is None:
                msg = f"source {source!r} has no episode data"
                raise ValueError(msg)

            if ep_count is not None:
                meta.episode_count = ep_count
                meta.updated_at = _utcnow()
                session.add(meta)
            await session.commit()

        return await self.sync_episodes(
            metadata_id,
            episodes,
            episode_count=ep_count,
            overwrite=True,
        )

    async def ensure_episode(
        self, metadata_id: int, *, season: int = 1, episode: int
    ) -> Episode:
        """按集号取得或创建空标题行; 供文件绑定."""
        found = await self.find_episode(metadata_id, season=season, episode=episode)
        if found is not None:
            return found
        async with self._session() as session:
            row = Episode(metadata_id=metadata_id, season=season, episode=episode)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return row
