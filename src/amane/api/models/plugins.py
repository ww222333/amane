from pydantic import BaseModel, Field

from ...plugins.api import FilmSourceTestResult
from ...plugins.manager import PluginLoadFailure
from ...plugins.models import PluginConfig, SourceDescriptor


class PluginConfigUpdate(BaseModel):
    enabled: bool | None = None
    config: dict[str, object] = Field(default_factory=dict)


class PluginTestRequest(BaseModel):
    """连通测试请求; ``config`` 覆盖已保存项后用于构造临时 provider, 不写回配置."""

    config: dict[str, object] = Field(default_factory=dict)


class PluginTestResponse(FilmSourceTestResult):
    """连通测试响应, 形状与 ``FilmSourceTestResult`` 相同."""


class PluginResponse(BaseModel):
    descriptor: SourceDescriptor
    config: PluginConfig
    config_schema: dict[str, object]
    path: str | None = None
    supports_test: bool = False


class PluginListResponse(BaseModel):
    items: list[PluginResponse]
    failures: list[PluginLoadFailure] = Field(default_factory=list)
