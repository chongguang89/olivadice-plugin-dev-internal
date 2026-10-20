# 02 事件钩子与生命周期

## Event 类的调用规则

事件触发时，框架在 **`<插件命名空间>.main.Event`** 中查找对应方法。例如命名空间为 `OlivaDiceCore` 的插件，收到私聊消息时会调用 `OlivaDiceCore.main.Event.private_message`。

所有钩子都是静态风格的方法（第一个参数不是 `self`），签名为 `(plugin_event, Proc)`。

```python
class Event(object):
    def init(plugin_event, Proc):
        start_scheduler_once()

    def group_message(plugin_event, Proc):
        handle_message(plugin_event, Proc, is_group=True)

    def private_message(plugin_event, Proc):
        handle_message(plugin_event, Proc, is_group=False)
```

不需要的钩子可以不写；保留了留空时写 `pass`。

## 事件全表

来源：OlivOS 官方文档 `https://doc.olivos.wiki/DevPlugin/Event/`（已逐条核实）。

### 消息事件

| 方法 | 触发时机 | data 字段 |
| --- | --- | --- |
| `group_message` | 收到群聊消息、频道消息 | `sub_type`、`host_id`（上层频道，缺省 `None`）、`group_id`、`user_id`、`sender`、`message`、`message_sdk`、`message_id`、`raw_message`、`raw_message_sdk` |
| `private_message` | 收到私聊消息 | `sub_type`、`user_id`、`sender`、`message`、`message_sdk`、`message_id`、`raw_message`、`raw_message_sdk` |

`message` 是**按插件 `message_mode` 转换后**的消息内容（青果插件一般就是带 `[OP:...]` 的字符串），`raw_message` 是未转换的消息源内容。

### 通知事件

| 方法 | 触发时机 | data 字段 |
| --- | --- | --- |
| `group_member_increase` | 群成员增加 | `group_id`、`operator_id`、`user_id`、`action`（`approve`=被同意放行 / `invite`=被邀请） |
| `group_member_decrease` | 群成员减少 | `group_id`、`operator_id`、`user_id`、`action`（`leave`=主动离开 / `kick`=被踢 / `kick_me`=骰子自己被踢） |
| `group_admin` | 群管理增减 | `group_id`、`user_id`、`action`（`set`=新增管理 / `unset`=移除管理） |
| `group_ban` | 群成员被禁言 | `group_id`、`operator_id`、`user_id`、`duration`（`0` 表示解除禁言） |
| `group_message_recall` | 群消息被撤回 | `group_id`、`operator_id`、`user_id`、`message_id` |
| `private_message_recall` | 私聊消息被撤回 | `user_id`、`message_id` |
| `group_file_upload` | 群文件上传 | `group_id`、`user_id`、`file`（含 `id` / `name` / `size` / `busid`） |
| `group_honor` | 群荣誉变更 | `group_id`、`user_id`、`type`（`talkative`=龙王 / `performer`=群聊之火 / `emotion`=快乐源泉） |
| `friend_add` | 添加了新好友 | `user_id` |
| `poke` | 被戳一戳 | `group_id`（私聊中为 `None`）、`user_id`（操作者）、`target_id`（被操作者） |
| `button_click` | QQ 官方机器人的回调按钮 | `user_id`、`group_id`、`button_id`、`button_data`、`message_id`、`extend`（含 `chat_type` / `chat_id`）。该事件**没有 `message`**，`reply()` 不支持，要用 `plugin_event.indeAPI.send_message(chat_type, chat_id, text)` 回包 |

**关于 `message_id`**：这个值**不一定是纯数字**——部分协议端版本返回的是 Base64 风格字符串（如 `ZboWS4aWxK9p...`）。一律当**不透明字符串**处理：不要 `int()`，不要用 `\d+` 类正则在消息文本里提取它，统一用 `([^,\]]+)`。详见 `references/03-messaging-and-api.md`。

### 请求事件

| 方法 | 触发时机 | data 字段 |
| --- | --- | --- |
| `group_add_request` | 收到加群请求 | `group_id`、`user_id`、`comment`（验证信息）、`flag`（调用处理 API 时必传） |
| `group_invite_request` | 收到加群邀请 | `group_id`、`user_id`、`comment`、`flag` |
| `friend_add_request` | 收到加好友请求 | `user_id`、`comment`、`flag` |

处理请求用：

```python
plugin_event.set_group_add_request(flag, "add", True, "")   # 同意加群
```

### 元事件

| 方法 | 触发时机 | 顺序保证 |
| --- | --- | --- |
| `init` | 本插件 `import` 流程完成后**立即**调用 | ⚠️ **不按优先级顺序** |
| `init_after` | 所有插件 `import` 完成后依次调用 | ✅ 一定按优先级顺序 |
| `save` | 加载器需要插件执行存储时（通常是即将重载前） | 全局重载时按优先级 |
| `menu` | 插件菜单被点击（含 WebUI 页面交互） | ✅ 按优先级 |

- `init` / `init_after` 的 `plugin_event` 可能是 `None`，**不要在 `init` 里访问 `plugin_event.data`**。
- `menu` 事件的 `plugin_event.bot_info` 为 `None`；WebUI 场景要回包得用 `plugin_event.send('webui', request_id, payload)`，不能用 `reply()`。

## plugin_event 成员

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `bot_info` | `bot_info_T` | 机器人信息 |
| `platform` | `dict` | `platform['platform']`（`qq`）、`platform['sdk']`（`onebot`）、`platform['model']` |
| `base_info` | `dict` | 内部使用，不要用 |
| `data` | — | 随事件类型不同，见上面的表 |

`bot_info_T`：

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `int` | 机器人 QQ 号（默认 -1） |
| `hash` | `str` | 机器人哈希值，用于查骰主列表等配置 |
| `platform` | `dict` | `sdk` / `platform` / `model` |
| `post_info` | `post_info_T` | 连接信息 |
| `extends` | `dict` | 扩展信息（可存自定义数据） |
| `debug_mode` | `bool` | 调试模式标志 |

`post_info_T`：

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `host` | `str` | 主机地址 |
| `port` | `int` | 端口号（默认 -1），调 HTTP API 用 |
| `access_token` | `str` / `None` | 访问令牌 |
| `type` | `str` | 服务器类型（默认 `post`） |
| `auto` | `bool` | 是否自动 |

## plugin_event 常用方法

| 方法 | 用途 |
| --- | --- |
| `plugin_event.reply(text)` | 原地回复（群聊、私聊都能用） |
| `plugin_event.send(type, target, text)` | 主动发送，`type` 取 `"group"` / `"private"`；WebUI 用 `"webui"` |
| `plugin_event.set_group_name(group_id, name)` | 改群名（批量改时必须限速） |
| `plugin_event.set_group_add_request(flag, "add", True, "")` | 同意加群申请 |
| `plugin_event.indeAPI.send_message(chat_type, chat_id, text)` | QQ 官方机器人特殊会话的发送 |

改群名、群名片、禁言、踢人、退群、撤回、删好友这类**管理动作**，青果没有逐一封装成 `plugin_event.xxx` 的，用 `api_request` 按 OneBot action 调（action 名与参数见 `references/api-index-*.md`）。**不管走哪个入口，都必须按 `references/04-risk-control.md` 串行 + 加间隔**，并且失败不重试。

## Proc：比 plugin_event 更可靠的信息源

`Proc` 是插件加载器的进程对象，**整个生命周期内不变**，可以赋值给插件里的全局变量随时使用。

关键成员：

```python
Proc.Proc_data['bot_info_dict']   # 已登录账号信息列表：key=bot 的 hash，value=bot_info_T
```

**这意味着：定时任务、跨会话主动发消息时，不必依赖"缓存最近一条 plugin_event"**——可以直接从 `Proc.Proc_data['bot_info_dict']` 拿到每个账号的 `post_info.port` / `access_token`，冷启动也能发消息。

需要时：

```python
_proc = None

def init(plugin_event, Proc):
    global _proc
    _proc = Proc      # 存下来，定时线程里用
```

`Proc` 的其余用法见官方文档「插件接口 → 进程接口」章节。

## 生命周期要点

- **`init` 可能被多次调用**，且不保证顺序。启动线程、注册调度这类动作必须用模块级标志防重入：

  ```python
  _started = False

  def init(plugin_event, Proc):
      global _started
      if _started:
          return
      _started = True
      start_scheduler()
  ```

- **不要依赖 `save` 落盘**。数据写入用 `setData` 立即写文件，`save` 里留空即可。
- **事件回调可能并发进入**，共享状态（模块级变量、数据文件）的读写必须加锁。这也是 `getData` / `setData` 内部带 `messagelock` 的原因。
- QQ 官方机器人（`qqGuildv2_link`）的事件（如 `button_click`）与普通 QQ 群事件差异较大，涉及时先单独确认需求，不要套用普通群聊的写法。
