"""按 updated_at 选取目标并扇出刮削. 影片 content_type 不存表, 运行时按路径或番号推断;
有所属库且库指定了 content_type 时固定该路由.
Metadata / Actor 各自判定, 不依赖挂载文件是否存在.
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from ..db import ActorSortField, TaskType
from ..db.models import Library, MediaFile, MetadataSortField, SortOrder
from ..parsing import infer_content_type
from .models import (
    ActorScrapePayload,
    CacheKind,
    RescrapePayload,
    RescrapeResult,
    RescrapeTarget,
    ScrapePayload,
    resolve_library_scrape_content_type,
)
from .protocol import FollowupTask, TaskHandler, TaskResult

if TYPE_CHECKING:
    from ..db.repository import Repository

_USE_CACHE = {CacheKind.metadata, CacheKind.trans}


class RescrapeHandler(TaskHandler[RescrapePayload, RescrapeResult]):
    def __init__(self, repo: Repository) -> None:
        super().__init__(payload_t=RescrapePayload, result_t=RescrapeResult)
        self._repo = repo

    async def handle(self, payload: RescrapePayload) -> TaskResult[RescrapeResult]:
        updated_before = (
            datetime.now(UTC) - timedelta(days=payload.min_age_days) if payload.min_age_days is not None else None
        )
        followups: list[FollowupTask] = []
        metadata_count = 0
        actor_count = 0

        if RescrapeTarget.metadata in payload.targets:
            meta_followups = await self._metadata_followups(payload.limit, updated_before)
            metadata_count = len(meta_followups)
            followups.extend(meta_followups)

        if RescrapeTarget.actor in payload.targets:
            actor_followups = await self._actor_followups(payload.limit, updated_before)
            actor_count = len(actor_followups)
            followups.extend(actor_followups)

        return TaskResult(
            success=True,
            result=RescrapeResult(submitted=metadata_count + actor_count, metadata=metadata_count, actors=actor_count),
            followups=followups,
        )

    async def _metadata_followups(self, limit: int, updated_before: datetime | None) -> list[FollowupTask]:
        items, _ = await self._repo.list_metadata(
            sort_by=MetadataSortField.UPDATED_AT,
            order=SortOrder.ASC,
            limit=limit,
            updated_before=updated_before,
        )
        identified = [(m, m.id) for m in items if m.id is not None]
        if not identified:
            return []

        # 挂载文件用于推断与库级路由: 每个 metadata 取第一个文件即可.
        files = await self._repo.list_media_files(metadata_ids=[mid for _, mid in identified], limit=None)
        first_file_by_metadata: dict[int, MediaFile] = {}
        for f in files:
            if f.metadata_id is not None and f.metadata_id not in first_file_by_metadata:
                first_file_by_metadata[f.metadata_id] = f

        lib_cache: dict[int, Library | None] = {}
        followups: list[FollowupTask] = []
        for meta, meta_id in identified:
            media = first_file_by_metadata.get(meta_id)
            path = media.path if media is not None else None
            inferred = infer_content_type(meta.number, path)
            library: Library | None = None
            if media is not None:
                if media.library_id not in lib_cache:
                    lib_cache[media.library_id] = await self._repo.get_library(media.library_id)
                library = lib_cache[media.library_id]
            content_type, locked = resolve_library_scrape_content_type(library, inferred=inferred)
            followups.append(
                FollowupTask(
                    key=f"scrape:{meta_id}",
                    task_type=TaskType.SCRAPE,
                    payload=ScrapePayload(
                        number=meta.number,
                        content_type=content_type,
                        use_cache=_USE_CACHE,
                        lock_content_type=locked,
                    ).model_dump(mode="json"),
                    priority=-1,
                )
            )
        return followups

    async def _actor_followups(self, limit: int, updated_before: datetime | None) -> list[FollowupTask]:
        actors = await self._repo.list_actors(
            sort_by=ActorSortField.UPDATED_AT,
            limit=limit,
            updated_before=updated_before,
        )
        return [
            FollowupTask(
                key=f"actor-scrape:{actor_id}",
                task_type=TaskType.ACTOR_SCRAPE,
                payload=ActorScrapePayload(actor_id=actor_id, use_cache=_USE_CACHE).model_dump(mode="json"),
                priority=-1,
            )
            for actor in actors
            if (actor_id := actor.id) is not None
        ]
