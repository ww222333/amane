# 相对上游的独有能力

> 对照基准: [sqzw-x/amane](https://github.com/sqzw-x/amane) 的 `main` (经 `upstream` 远端跟踪).
> 本文只列**本仓库相对该上游多出的产品能力**. 机制细节见交叉链接; 字段与签名以源码 / OpenAPI 为准.
> 上游已有且本仓库已并入的能力 (播放、Android 客户端、LLM、桌面环境变量配置等) 不在此重复.

## 未知内容类型与路由

- 解析无法识别番号 / 文件名时, 内容类型为 `unknown` (上游对应回退为 `western`).
- `content_routes.unknown` 可单独配置站点链; 默认空列表, 未配置则该类型刮削不请求任何站.

见 [content-routes.md](content-routes.md)、[config.md](config.md).

## 内容路由自定义前缀

- 每个内容类型的路由为 `{sites, prefixes}`, 而非仅站点列表.
- `prefixes` 命中番号时, 覆盖推断出的 `content_type`, 并采用该类型的 `sites` (多命中取最长前缀).

见 [config.md](config.md)、[task-system.md](task-system.md)「建图」.

## 整理失败目录

媒体库字段:

| 能力 | 说明 |
|------|------|
| `fail_dir` | 库根下单层失败目录名; 库表单可用路径选择器填写 |
| `move_to_fail_dir` | 整理时无 Metadata 的正片整夹移入该目录 |
| `exclude_fail_dir` | `fail_dir` 非空时, 扫描 / 监控 / 整理剪枝跳过该目录 |

任务 payload 可覆盖 `move_to_fail_dir`. 见 [task-system.md](task-system.md) `ORGANIZE`、用户文档 [libraries.md](../user/libraries.md).

## 整理空源回收

- 库级 `trash_empty_source`; 整理任务 payload 可覆盖.
- 为真时: 整理后全库扫描, 将递归无视频的目录整夹移入 `.amane_trash`.
- 不碰库根、回收站目录、刮削失败输出目录 (`fail_dir`).

见 [task-system.md](task-system.md) `ORGANIZE`.

## 插件连通测试

- 影片元数据插件可选声明 `supports_connectivity_test` 并实现 `FilmSourceProvider.test`.
- `POST /api/plugins/{id}/test` 用当前 (可覆盖) 配置临时构造 provider 做连通 / Cookie 检查, 不入队、不写配置.
- 仅声明支持的插件在配置页显示测试按钮; 内置站点不走此接口.

见 [plugins.md](plugins.md).

## 版本线

本仓库 CHANGELOG 在上游 `0.16.x` 条目之上, 另以 `v1.0.x` 记录上述独有能力的发版说明.
