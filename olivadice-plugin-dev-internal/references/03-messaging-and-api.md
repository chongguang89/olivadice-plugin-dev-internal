# 03 消息构造与 API 调用

## 两种发送方式

| 方式 | 用法 | 适用场景 |
| --- | --- | --- |
| 原地回复 | `plugin_event.reply("内容")` | 回复当前会话；群聊、私聊通用 |
| 主动发送 | `plugin_event.send("group", groupid, "内容")`<br>`plugin_event.send("private", uid, "内容")` | 发给别的群 / 别的窗口，或定时任务主动推送 |

## @ 人的格式（硬规则）

| 场景 | 格式 |
| --- | --- |
| **收到的消息**里 @ 的呈现 | `[OP:at,id=<QQ号>]`，通常出现在句尾，例如「删除恋综xxx[OP:at,id=123456]」 |
| **异群、异窗口主动构造**的消息（`send`） | `[CQ:at,qq=<QQ号>]` |
| **原地回复**（`reply`）里构造的消息 | `[OP:at,id=<QQ号>]` |

解析收到的 @ 时用兼容正则：

```python
m = re.search(r"\[(?:OP|CQ):at,(?:id|qq)=(\d+)\]", message)
```

## 指令风格：先问用户要哪一种

两种常见风格，**动笔前必须问用户选哪种**，不要两套一起上：

| 风格 | 长什么样 | 匹配方式 |
| --- | --- | --- |
| 固定文本直接触发 | `排单`、`查单`、`还单 1234` | 直接 `startswith` / `re.match` 原消息 |
| 符号前缀触发 | `.排单`、`/查单`（`.` 和 `/` 都认） | 先剥前缀，再匹配 |

符号前缀的剥离：

```python
cmd = re.sub(r"^(?:\.|/|／|．)", "", message).strip()
```

全角 `／`、`．` 是否一起认，取决于用户群里的习惯——问一句再决定，别默认全兼容。

**固定文本风格的注意点**：

- 指令词要足够独特，否则会被闲聊误触。"发送""查""改"这种单字或常见动词尤其危险——用户群里随口说一句就会命中。
- 长指令词要排在短的之前匹配（`还单` 先于 `还`），否则长指令会被短前缀截胡。

**符号前缀风格的注意点**：

- 用户说"用点号"时，确认一下要不要同时认 `/`——同一个群里不同人习惯不同。
- 剥完前缀记得 `.strip()`。

选定之后**全插件保持一致**：带了前缀就所有指令都带，不要有的带有的不带。

## 引用了别的消息时：先剥离，再匹配指令

QQ 里"引用一条消息再发指令"时，收到的 `message` **开头会多一个 reply 段**：

```
[OP:reply,id=-1234567890]
[OP:reply,id=ZboWS4aWxK9pQ2mR7tL]      ← 某些版本是这种 Base64 风格字符串
```

拿这个原始 `message` 直接去 `startswith("指令")` 或 `re.match`，**永远匹配不上**——第一个字符是 `[`，不是指令词。所以凡是"引用消息 + 指令"的指令，第一步必须把 reply 段剥掉再匹配：

```python
clean_message = re.sub(r"^\[(?:OP|CQ):reply,id=[^,\]]+\]", "", message).strip()

if not clean_message.startswith("指令"):
    return
```

### message_id 不一定纯数字（硬规则）

部分协议端、部分版本的 `message_id` 已经从纯数字变成 **Base64 风格字符串**（`ZboWS4aWxK9p...`，大小写字母+数字，可能带 `-` `_`）。仍然按"负数或正数"写 `[-]?\d+` 就会匹配失败，插件表现为指令完全没反应。所以：

- 匹配 id 的正则**统一写成 `([^,\]]+)`**（一直吃到 `,` 或 `]` 为止），不要写 `\d+`、`[-]?\d+`、`[+-]?\d+`。
- 取出来的 id **当字符串用，不要 `int()`**——遇到 Base64 id 会直接 `ValueError` 崩掉。`{"message_id": reply_id}` 这样传就行。
- 同一个插件里所有匹配 id 的地方（reply、forward、撤回、`get_msg`、合并转发）**用同一套宽松正则**，不要有的宽有的窄——否则就会出现"有的指令能用、有的没反应"的怪现象。

```python
m = re.search(r"\[(?:OP|CQ):reply,id=([^,\]]+)\]", message)
reply_id = m.group(1)      # 字符串，直接进 payload
```

要点：

- **只剥开头**（`^` 锚定）。引用段只会出现在最前面，别用不带锚定的 `re.sub` 去扫全文，会误伤正文里恰好长得像关键字的内容。
- 剥完 `.strip()` 一次，避免指令前残留空格导致匹配失败。
- **无条件先剥是安全的**：不带引用的消息本来就没有这个前缀，`re.sub` 不会改动它。所以这条可以直接写进消息入口，不用额外判断。
- 这套只在用户明确提到"要引用某条消息再操作"时才需要。纯文本指令直接匹配原 `message` 就行。

### 如果还要读被引用那条消息的内容

只剥前缀是不够的——比如"引用一张登记表再回复指令，从表里提取字段"。这时要拿 `reply_id` 去调 `get_msg` 把原消息拉回来：

1. **从原始 `message` 里 `re.search` 出 id**，别从 `clean_message` 里找，已经被剥掉了。
2. 没引用时要**明确提示**用户「请引用 XX 再发送指令」，不要静默 return——用户不知道哪里错了。
3. 拉回来的内容可能是**消息段数组**，也可能是 **CQ 字符串**，两种格式都要能取到纯文本。
4. 接口调用方式按协议端文档来（`references/08-api-lookup.md`），用的就是 `bot_info.post_info.port` + `access_token` 走 HTTP。**具体封装按本插件需要写，不要照抄别人的实现。**

### 引用的会不会是合并转发（forward）消息

reply 和 forward 是**两种不同的段**，别混：

| 段 | 长什么样 | 读它用什么 |
| --- | --- | --- |
| reply | `[OP:reply,id=...]`，表示"引用了某条消息" | `get_msg`，传 reply 的 id |
| forward | `[OP:forward,id=...]` / `[CQ:forward,id=...]`，表示"这是一张合并转发卡片" | `get_forward_msg`，传 forward 的 id |

坑在**引用合并转发卡片**的时候：`reply` 段里的 id 有时拿到的是那条 forward 消息本身的 id。丢给 `get_msg` 不会报错，但返回的往往只是个**外壳**——里面只有一个 forward 段，聊天记录一条都看不到。

**所以涉及"引用消息"的需求，必须先问用户一句：这条被引用的消息会不会是合并转发？** 会的话才需要下面这层解析，不会就别写，多一层只会让代码更绕。

需要解析时的稳妥顺序（不靠猜，靠逐个试）：

1. `get_msg` 把被引用的消息拉回来；
2. 在它的 `raw_message` 里找 `[OP|CQ:forward,id=...]`（`raw_message` 可能是字符串，也可能是以 CQ 文本为 key 的 dict，两种都试一下）；找到就把这个 forward_id 加进候选；
3. 候选列表 = `[reply_id, forward_id]`，依次丢给 `get_forward_msg`，哪个先返回 `retcode == 0` 且带 `data.messages` 就用哪个；
4. 展开后每条消息的字段名在两套协议端不统一，取文本要逐个兜底：`message` 数组（标准 / NapCat）→ `content` 数组（LLBot 旧版）→ `raw_message` → `text`。

注意：

- **两个 id 都可能不是纯数字**，全链路都按字符串处理（见上面「message_id 不一定纯数字」）。
- `get_forward_msg` 偶尔会因为转发过期或服务端延迟失败，要不要重试、重试几次按用户需求定；**但别写"无限重试到成功"**，失败就明确告诉用户"这张转发读不到，请重新转发一次"。
- 拉回来的内容可能很长，别直接 `reply` 出去，按 `references/03` 的长文本规则处理或改合并转发。

## 图片

**存放位置是硬规则**：图片必须生成/保存到与 `plugin/` 同级的 `data/images/<插件名>/` 下（注意是 `images` 复数），再按文件名引用。详见 `references/06-image-rendering.md`。

发送有两条路，写法不同，别混：

```python
# 1) 直发（不在合并转发里）：file= 填相对 ./data/images/ 的路径，不带前缀
plugin_event.reply(f"分享码如下：\n[CQ:image,file=我的插件/二维码/qr.png]")

# 2) 放在合并转发节点里：file= 填 file:// 绝对路径
{"type": "image", "data": {"file": f"file://{os.path.abspath(img_path)}"}}
```

## 合并转发

构造合并转发的节点时：

- **发件人必须用骰子自己的 `uin` 和 `nickname`**，不能用消息发送者或其他用户的 id 与昵称。
- 单次节点数 **≤ 90**，常规取 **70**；超过就分块，块与块之间 `time.sleep(2)`。
- 群聊用 `send_group_forward_msg`，私聊用 `send_private_forward_msg`。

`templates/main.py` 里已有 `send_forward_message()` 可直接用，节点结构：

```python
nodes = [
    {"bot_id": bot_id, "bot_nickname": "骰子昵称", "content_text": "第一段"},
    {"bot_id": bot_id, "content_list": [{"type": "text", "data": {"text": "第二段"}}]},
]
```

## 长文本与多段回复

- 内容太长不要硬塞一条：拆成多个节点走合并转发。
- 需要在同一会话连发多条时，**每条之间 `time.sleep(1)`**（帮助信息、结果分条播报等）。

## 特殊消息必须直接调 API

有些消息类型 `plugin_event.send` 发不了，必须绕过封装直接打骰子的 HTTP 接口，例如音乐卡片：

```python
payload = {
    "group_id": int(group_id),
    "message": [{"type": "music", "data": {"type": "163", "id": song_id}}],
}
api_request(bot_port, bot_token, "send_group_msg", payload, plugin_event)
```

同类还有需要精细控制消息段（图片、文件、自定义 json/xml 卡片）的场景。判断标准：`plugin_event.send` 里用 CQ 码写不出来的，就走 HTTP。

## API 封装

`templates/main.py` 里的 `api_request()` 是统一入口：

```python
def api_request(bot_port, bot_token, endpoint, payload, plugin_event=None):
    url = f"http://127.0.0.1:{bot_port}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }
    ...
```

要点：

- 端口和 token 从 `plugin_event.bot_info.post_info` 取，同一插件里可以封装成"一次取好、多处复用"。定时任务等拿不到 `plugin_event` 的场景，可用 `Proc.Proc_data['bot_info_dict']`（见 `references/02-events-and-lifecycle.md`）。
- `timeout` 取 5～10 秒；合并转发这类重接口取 10 秒。
- 判定成功看 `retcode == 0`。
- 失败时把 `message` 或 `wording` 取出来，用 `plugin_event.reply` 反馈给用户，**不要静默吞掉**。
- 已核实的 `retcode` 语义（NapCat BaseResponse，LLBot 同一套约定）：`0` 成功；`1400` 请求参数错误或业务逻辑执行失败；`1401` 权限不足；`1404` 资源不存在。限流类失败不要写自动重试，只会扩大风控面（见 `references/04-risk-control.md`）。
- **接口路径和参数不要凭记忆写**：查 `references/08-api-lookup.md` 的流程，索引里有每个接口的文档直链，抓 `.md` 就能拿到 body 参数和示例。

常用端点：

| 端点 | 用途 |
| --- | --- |
| `send_group_msg` / `send_private_msg` | 发消息（支持消息段数组） |
| `send_group_forward_msg` / `send_private_forward_msg` | 合并转发 |
| `get_msg` | 按 `message_id` 取单条消息（解析引用消息用） |
| `get_forward_msg` | 按 forward id 展开合并转发，内容在 `data.messages` |
| `get_stranger_info` | 查昵称等陌生人信息（传 `{"user_id": int(qq)}`） |
| `get_login_info` | 取骰子自己的昵称（合并转发节点要用） |

**`get_msg` / `get_forward_msg` 的 `message_id` 一律按字符串传**（`{"message_id": msg_id}`），不要 `int()`——id 可能是 Base64 字符串。

协议参考文档：

- 接口索引与查询流程见 `references/08-api-lookup.md`（内置 `api-index-luckylillia.md` 与 `api-index-napcat.md` 两份快照，每条接口带可抓取的 `.md` 文档直链）。
- napcat 文档站：`https://napcat.apifox.cn`
- LLBot 文档站：`https://api.luckylillia.com/doc-5416163`

两套协议都是 OneBot 实现，标准接口名一致；**扩展接口差异大，且同名字段类型可能不同**，调用前逐个查文档，不要猜。

## 昵称与群名

查昵称、群名要发 HTTP 请求，属于耗时操作：查询结果可以按需做内存缓存（例如存最近 100 条），但这是性能优化、不是强制要求，按实际调用频率决定。
