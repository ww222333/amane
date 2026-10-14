"""Kodi NFO: 影片 ``<movie>``; 漫剧 ``<tvshow>`` / ``<episodedetails>``."""

import re
from io import StringIO
from typing import TYPE_CHECKING

import aiofiles
import structlog

from ..utils.text import strip_illegal_xml_chars

if TYPE_CHECKING:
    from pathlib import Path

    from ..db.models import Episode, Metadata


logger = structlog.get_logger()


_XML_ESCAPE_MAP: dict[str, str] = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&apos;",
    '"': "&quot;",
}


def _escape_xml(text: str) -> str:
    """写进 XML 文本节点: 先剥非法字符 (存量脏数据兜底), 再转义; 换行原样保留."""
    escaped = strip_illegal_xml_chars(text)
    for char, entity in _XML_ESCAPE_MAP.items():
        escaped = escaped.replace(char, entity)
    return escaped


def _write_year_and_dates(code: StringIO, release: str | None) -> None:
    if not release:
        return
    code.write(f"  <premiered>{release}</premiered>\n")
    code.write(f"  <releasedate>{release}</releasedate>\n")
    year_match = re.match(r"(\d{4})", release)
    if year_match:
        code.write(f"  <year>{year_match.group(1)}</year>\n")


def _write_actors(code: StringIO, actors: list[str]) -> None:
    for actor in actors:
        if not actor:
            continue
        code.write("  <actor>\n")
        code.write(f"    <name>{_escape_xml(actor)}</name>\n")
        code.write("    <type>Actor</type>\n")
        code.write("  </actor>\n")


def _write_tags(code: StringIO, tags: list[str]) -> None:
    for tag in tags:
        if tag:
            code.write(f"  <tag>{_escape_xml(tag)}</tag>\n")
            code.write(f"  <genre>{_escape_xml(tag)}</genre>\n")


async def _flush_nfo(nfo_path: Path, body: str) -> bool:
    try:
        nfo_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(nfo_path, "w", encoding="UTF-8") as f:
            await f.write(body)
        logger.debug("nfo written", path=str(nfo_path))
        return True
    except Exception:
        logger.exception("nfo write failed", path=str(nfo_path))
        return False


async def write_nfo(metadata: Metadata, nfo_path: Path) -> bool:
    """影片库: ``<movie>``."""
    try:
        code = StringIO()
        code.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        code.write("<movie>\n")

        if metadata.plot:
            plot_escaped = _escape_xml(metadata.plot)
            code.write(f"  <plot>{plot_escaped}</plot>\n")
            code.write(f"  <outline>{plot_escaped}</outline>\n")

        _write_year_and_dates(code, metadata.release)
        code.write(f"  <num>{_escape_xml(metadata.number)}</num>\n")

        if metadata.title:
            code.write(f"  <title>{_escape_xml(metadata.number)} {_escape_xml(metadata.title)}</title>\n")
            code.write(
                f"  <originaltitle>{_escape_xml(metadata.number)} {_escape_xml(metadata.title)}</originaltitle>\n"
            )
            code.write(f"  <sorttitle>{_escape_xml(metadata.number)} {_escape_xml(metadata.title)}</sorttitle>\n")

        code.write("  <mpaa>JP-18+</mpaa>\n")
        _write_actors(code, metadata.actors)

        if metadata.score is not None:
            code.write(f"  <rating>{metadata.score}</rating>\n")
            code.write(f"  <criticrating>{int(metadata.score * 10)}</criticrating>\n")

        if metadata.runtime is not None:
            code.write(f"  <runtime>{metadata.runtime}</runtime>\n")

        if metadata.series:
            code.write(f"  <series>{_escape_xml(metadata.series)}</series>\n")
            code.write("  <set>\n")
            code.write(f"    <name>{_escape_xml(metadata.series)}</name>\n")
            code.write("  </set>\n")

        if metadata.studio:
            code.write(f"  <studio>{_escape_xml(metadata.studio)}</studio>\n")
            code.write(f"  <maker>{_escape_xml(metadata.studio)}</maker>\n")

        if metadata.publisher:
            code.write(f"  <publisher>{_escape_xml(metadata.publisher)}</publisher>\n")
            code.write(f"  <label>{_escape_xml(metadata.publisher)}</label>\n")

        _write_tags(code, metadata.tags)

        if metadata.poster_url:
            code.write(f"  <poster>{_escape_xml(metadata.poster_url)}</poster>\n")

        if metadata.thumb_url:
            code.write(f"  <cover>{_escape_xml(metadata.thumb_url)}</cover>\n")

        if metadata.trailer_url:
            code.write(f"  <trailer>{_escape_xml(metadata.trailer_url)}</trailer>\n")

        if metadata.directors:
            for director in metadata.directors:
                code.write(f"  <director>{_escape_xml(director)}</director>\n")

        if metadata.external_ids:
            for site, ext_id in metadata.external_ids.items():
                if ext_id:
                    code.write(f"  <{site}id>{_escape_xml(str(ext_id))}</{site}id>\n")

        code.write("</movie>\n")
        return await _flush_nfo(nfo_path, code.getvalue())
    except Exception:
        logger.exception("nfo write failed", path=str(nfo_path))
        return False


async def write_tvshow_nfo(metadata: Metadata, nfo_path: Path) -> bool:
    """漫剧剧级: ``<tvshow>``."""
    try:
        code = StringIO()
        code.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        code.write("<tvshow>\n")
        show_title = (metadata.title or metadata.number or "").strip() or metadata.number
        code.write(f"  <title>{_escape_xml(show_title)}</title>\n")
        code.write(f"  <originaltitle>{_escape_xml(show_title)}</originaltitle>\n")
        code.write(f"  <sorttitle>{_escape_xml(show_title)}</sorttitle>\n")
        code.write(f"  <showtitle>{_escape_xml(show_title)}</showtitle>\n")
        if metadata.plot:
            plot_escaped = _escape_xml(metadata.plot)
            code.write(f"  <plot>{plot_escaped}</plot>\n")
            code.write(f"  <outline>{plot_escaped}</outline>\n")
        _write_year_and_dates(code, metadata.release)
        if metadata.episode_count is not None:
            code.write(f"  <episodeguide>{metadata.episode_count}</episodeguide>\n")
            code.write(f"  <season>1</season>\n")
            code.write(f"  <episode>{metadata.episode_count}</episode>\n")
        if metadata.studio:
            code.write(f"  <studio>{_escape_xml(metadata.studio)}</studio>\n")
        _write_tags(code, metadata.tags)
        _write_actors(code, metadata.actors)
        if metadata.poster_url:
            code.write(f"  <thumb>{_escape_xml(metadata.poster_url)}</thumb>\n")
        if metadata.thumb_url:
            code.write(f"  <fanart>{_escape_xml(metadata.thumb_url)}</fanart>\n")
        code.write(f"  <uniqueid type=\"amane\" default=\"true\">{_escape_xml(metadata.number)}</uniqueid>\n")
        code.write("</tvshow>\n")
        return await _flush_nfo(nfo_path, code.getvalue())
    except Exception:
        logger.exception("tvshow nfo write failed", path=str(nfo_path))
        return False


async def write_episode_nfo(
    metadata: Metadata,
    nfo_path: Path,
    *,
    season: int = 1,
    episode: int,
    episode_row: Episode | None = None,
) -> bool:
    """漫剧单集: ``<episodedetails>``."""
    try:
        code = StringIO()
        code.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        code.write("<episodedetails>\n")
        show_title = (metadata.title or metadata.number or "").strip() or metadata.number
        ep_title = None
        ep_plot = None
        if episode_row is not None:
            ep_title = (episode_row.title or "").strip() or None
            ep_plot = (episode_row.plot or "").strip() or None
        display_title = ep_title or f"第 {episode} 集"
        code.write(f"  <title>{_escape_xml(display_title)}</title>\n")
        code.write(f"  <showtitle>{_escape_xml(show_title)}</showtitle>\n")
        code.write(f"  <season>{season}</season>\n")
        code.write(f"  <episode>{episode}</episode>\n")
        plot = ep_plot or metadata.plot
        if plot:
            code.write(f"  <plot>{_escape_xml(plot)}</plot>\n")
        _write_year_and_dates(code, metadata.release)
        if metadata.runtime is not None:
            code.write(f"  <runtime>{metadata.runtime}</runtime>\n")
        _write_actors(code, metadata.actors)
        if metadata.studio:
            code.write(f"  <studio>{_escape_xml(metadata.studio)}</studio>\n")
        code.write(
            f"  <uniqueid type=\"amane\" default=\"true\">{_escape_xml(metadata.number)}-S{season:02d}E{episode:02d}</uniqueid>\n"
        )
        code.write("</episodedetails>\n")
        return await _flush_nfo(nfo_path, code.getvalue())
    except Exception:
        logger.exception("episode nfo write failed", path=str(nfo_path))
        return False
