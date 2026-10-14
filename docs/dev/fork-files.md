# 相对上游的改动文件

> 对照基准: [sqzw-x/amane](https://github.com/sqzw-x/amane) 的 `main` (`upstream`).
> 产品能力说明见 [fork-delta.md](fork-delta.md). 本文只列**实现这些独有能力时相对上游有差异的路径**; 标识符与签名以源码为准.
> 插件实现 (`mdcx.huangguoai` / `mdcx.javday` 等) 在独立仓库, 不在本树.

## 未知 / 漫剧类型与内容路由前缀

| 路径 | 角色 |
|------|------|
| `src/amane/parsing/file_info.py` | `manju` / `unknown` 解析; 剥季集尾标 |
| `src/amane/config/manager.py` | `{sites, prefixes}`、默认漫剧链 |
| `src/amane/handlers/scrape.py` | 刮削按路由取站 |
| `src/amane/handlers/refresh.py` | 刷新侧类型与路由 |
| `src/amane/crawlers/connectivity.py` | 网络检测遍历 `entry.sites` |
| `web/src/lib/exhaustive-maps.ts` | 前端内容类型枚举 |
| `web/src/i18n/locales/*/metadata.json` | `manju` / `unknown` 文案 |
| `web/src/i18n/locales/*/settings.json` | 设置页类型文案 |
| `web/src/i18n/locales/*/library.json` | 库侧类型文案 |
| `web/src/i18n/locales/*/feeds.json` | Feed 类型文案 |
| `web/src/i18n/locales/*/tasks.json` | 任务覆盖类型文案 |
| `docs/dev/content-routes.md` | 路由契约 |
| `docs/dev/config.md` | 配置契约 |
| `tests/parsing/test_file_info.py` | 解析测试 |

## 整理失败目录与空源回收

| 路径 | 角色 |
|------|------|
| `src/amane/db/models.py` | 库表字段 |
| `src/amane/db/repo_types.py` | 仓储类型 |
| `src/amane/db/repos/libraries.py` | 库读写 |
| `src/amane/api/models/libraries.py` | API 模型 |
| `src/amane/api/routes/libraries.py` | API 路由 |
| `src/amane/library/rules.py` | 失败目录规则 |
| `src/amane/library/scan.py` | 扫描剪枝 |
| `src/amane/library/__init__.py` | 导出 |
| `src/amane/handlers/file.py` | ORGANIZE: 移入失败目录 / 空源回收 |
| `src/amane/handlers/models.py` | 任务 payload 覆盖字段 |
| `src/amane/scheduler/watcher.py` | 监控跳过 `fail_dir` |
| `src/amane/scheduler/service.py` | 调度侧衔接 |
| `src/amane/db/migrations/versions/887ba98287ed_library_fail_dir.py` | `fail_dir` 迁移 |
| `src/amane/db/migrations/versions/e6c559a3f203_library_trash_empty_source.py` | `trash_empty_source` 迁移 |
| `src/amane/db/migrations/versions/836b567fc54c_merge_fork_library_columns_with_.py` | 与上游迁移线合并 |
| `src/amane/db/migrations/versions/fdd597ef57cc_merge_fork_fail_dir_with_upstream_kin8.py` | 再合并上游 kin8 线, 保证单一 head |
| `web/src/components/library/library-form.tsx` | 库表单 |
| `web/src/components/path-picker/path-picker.tsx` | 失败目录路径选择 |
| `web/src/i18n/locales/*/library.json` | 库字段文案 |
| `web/src/i18n/locales/*/tasks.json` | 任务覆盖文案 |
| `docs/user/libraries.md` | 用户说明 |
| `tests/library/test_rules.py` | 规则测试 |

## 插件连通测试

| 路径 | 角色 |
|------|------|
| `src/amane/plugins/api.py` | `supports_connectivity_test` / `test` |
| `src/amane/plugins/manager.py` | 装配 |
| `src/amane/api/models/plugins.py` | 请求 / 响应模型 |
| `src/amane/api/routes/plugins.py` | `POST /api/plugins/{id}/test` |
| `web/src/hooks/use-plugins.ts` | `useTestPlugin` |
| `web/src/components/plugins/plugin-settings-dialog.tsx` | 配置页测试按钮 |
| `web/src/i18n/locales/*/plugins.json` | 测试文案 |
| `web/openapi.json` | OpenAPI |
| `web/src/client/` | 生成客户端 (含 `testPlugin`) |
| `docs/dev/plugins.md` | 契约 |
| `tests/api/test_plugins.py` | API 测试 |

## 插件本地封面 (`amane-local:`)

| 路径 | 角色 |
|------|------|
| `src/amane/media/resource_store.py` | locator 解析与拷入 resources |
| `src/amane/media/pipeline.py` | 成功项改写为 `/api/resources/{hash}` |
| `docs/dev/data-model.md` | Resource locator 契约 |
| `docs/dev/plugins.md` | 插件交付约定 |
| `tests/media/test_resource_store.py` | 存储测试 |
| `tests/media/test_pipeline.py` | 管线测试 |

## 请求级 TLS 指纹

| 路径 | 角色 |
|------|------|
| `src/amane/net/http.py` | `request(..., impersonate=...)` |
| `tests/net/test_http.py` | 测试 |

## 索引与发版线

| 路径 | 角色 |
|------|------|
| `docs/dev/fork-delta.md` | 独有能力说明 |
| `docs/dev/index.md` | 开发文档入口 |
| `CHANGELOG.md` | `v1.0.x` 条目 (上游为 `v0.x`) |

## 仓库外

| 位置 | 角色 |
|------|------|
| `amane-mdcx-plugins` (独立仓库) | `mdcx.huangguoai` 解密封面与 `amane-local`; `mdcx.huangguodrama` (huangguodrama.ai HTML); `mdcx.javday` 漫剧 / 简繁等 |
