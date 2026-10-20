# 08 协议 API 查询方法

两套协议（napcat / LLBot）的接口文档**agent 可以自行获取**，不需要用户手动复制。本文件规定查询流程。

## 索引文件（快照）

skill 内置了两份接口索引，每一条都带可直接抓取的 `.md` 文档链接：

| 文件 | 协议 | 快照日期 |
| --- | --- | --- |
| `references/api-index-luckylillia.md` | LLBot（幸运莉莉娅，OneBot 11） | 2026-10-15 |
| `references/api-index-napcat.md` | NapCat | 2026-10-15 |

索引条目格式：`- 分类 [接口名](文档直链): 备注`。备注里常标注版本要求（如「此 API 需要 LLBot 8.0.3 及以上版本」），**写代码前必须提醒用户确认骰子的协议端版本**。

## 查询流程

**第 0 步（每次都要做）：先问清楚协议端。** 骰子挂的是 napcat 还是 LLBot？协议端版本是多少？不确认就直接写，等于赌博——两边扩展接口不通用、同名字段类型也不同。这一步属于需求澄清的必问项，不得跳过、不得假设。

需要调用某个接口时，按此顺序：

1. **在索引里找接口**（两个索引都查，确认两边的路径与参数）。
2. **抓取该接口的 `.md` 文档链接**（索引里的 URL 直接就是 markdown 版文档），能得到完整的 OpenAPI 定义：body 参数（名称/类型/必需/说明）、请求示例、成功与失败响应示例。
3. 按文档写 `api_request(...)` 调用，参数严格照抄文档字段名，**不要自己拼字段**。
4. 索引里没有的接口、或抓取失败时，**停下来问用户**，请对方把该接口页面的 **Body 参数、请求示例代码、返回成功响应**复制或截图发来（接口页右上角有一键复制按钮）。拿到后再写代码。

**禁止**：凭记忆或常识猜测接口路径与参数。OneBot 11 只是"大体一致"，两边的字段类型、必需项、返回结构都有差异，一切以抓到的文档为准。

## 两协议的差异点（实测确认过）

- 同一接口的**字段类型可能不同**。例如 `set_group_admin`：LLBot 的 `group_id` / `user_id` 是 `integer` 且全部必需；NapCat 的同名参数是 `string`，`enable` 可以是 boolean 或 string。写代码时按各自文档来，不要混用。
- **响应结构不同**：
  - LLBot 成功时看 `retcode == 0`。
  - NapCat 的 BaseResponse 含 `status`（ok/failed）、`retcode`、`data`、`message`、`wording`、`stream`；失败码语义：`1400` 参数错误或业务失败、`1401` 权限不足、`1404` 资源不存在。
- NapCat 有一批**独有扩展接口**（群相册、群打卡、戳一戳、AI 语音、QQ 空间、流式传输文件等）；LLBot 也有自己的扩展（超级表情、Ai 语音、表情回应等）。**用了哪边的独有接口，插件就只兼容那一边**，必须在更新日志里注明，并在代码里对另一边做好失败提示。
- **`message_id` 的类型会变**：部分协议端版本已从纯数字改成 Base64 风格长字符串（如 `ZboWS4aWxK9p...`）。插件里一律当字符串处理，别 `int()`、别用 `\d+` 提取（见 `references/03-messaging-and-api.md` 的「message_id 不一定纯数字」）。这是**静默失效**型故障：正则匹配不上就没有异常，只是指令完全不响应。
- LLBot 文档明确：HTTP 调用需在 LLBot 客户端里开启 OneBot HTTP 服务；SSE 长连接（`/_events`）需要 4.7.3+。

## 通用规范（OneBot 11 基础接口）

发送消息、撤回、获取登录号信息等 OneBot 11 标准接口两边都有，路径一致（`/send_group_msg`、`/send_private_msg`、`/delete_msg`、`/get_login_info`、`/get_stranger_info`、合并转发 `/send_group_forward_msg` 等）。标准接口可以直接写；**扩展接口**才需要逐个查文档。

鉴权统一是 HTTP Header：`Authorization: Bearer <token>`，token 来自 `plugin_event.bot_info.post_info.access_token`。

## 索引过期了怎么办

协议端更新会新增接口。如果索引里找不到需要的接口：

1. 先尝试让用户重新从文档站导出（两个站点都有「LLMs.txt」入口，提供全站 API 文档的 markdown 索引）；
2. 或者让用户直接贴该接口的 Body 参数 + 请求示例 + 成功回执。

把新的索引文件替换 `references/api-index-*.md`，并更新本文件的快照日期。
