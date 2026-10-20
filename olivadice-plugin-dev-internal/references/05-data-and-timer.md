# 05 数据读写与定时任务

## 数据存放

```python
datafile = "插件英文名"   # 与插件名一致，保持英文
```

数据文件位置：`./plugin/data/<datafile>/<文件名>.json`。**不要**把数据写进插件文件夹，也不要把数据文件打进 opk。

数据文件名由你自己定，按业务命名（`config.json`、`orders.json`、`privategroup.json`…… 随便取）。

**插件数据目录下可以再分子目录**，两种写法都行：

```python
# 写法 A：路径参数就一个，直接传带子目录的相对路径（改动最小）
getData(f"vendors/{group_id}.json")
setData(f"quotas/{uid}.json", data)

# 写法 B：拆成两个参数（业务域 + 文件名）
def getData(folder, filename):   # getData("engagement", "appoint.json")
```

写法 A 需要在 `setData` 里补上自动建目录的两行，见下面「实现细节」。

**不管用哪种写法，锁的逻辑和 `.bak` 机制都不要改动。**

## 数据建模：按实际情况分，但必须封顶

`getData` / `setData` 是**全量读、全量写**：每次读取把整个文件 `json.load` 进内存，每次写入整个文件重写一遍，而且**没有原子写入**。大文件会同时带来三个问题：性能（每次读写都变慢，拖累消息处理）、风险（写入出意外整个文件一起遭殃）、难维护（几千行 json 里翻数据是灾难）。

**怎么分没有标准答案**——取决于这个插件的数据主体、访问模式和保留策略。同一个插件的不同业务，用不同分法是完全正常的；数据量小的时候不拆也对。**不要照搬别的插件的数据结构，按当前插件的实际情况决定。**

### 三条硬约束（不可协商）

1. **不许无限增长**：任何数据文件都不能设计成"只增不减"。设计阶段就要能回答"它最终会有多大"。
2. **必须留清理出口**：在**设计时**就定好——什么时候删、由谁触发删、删多少。不能留一句"以后再说"。
3. **不许读放大**：消息处理路径上不能反复全量读一个大文件（每条消息都读全量 = 最坏组合）。

### 动手前先问清三件事

这三个答案是分法的基础，**问不出来就去问用户，不要自己假设**：

1. **数据主体是谁**——用户？群？独立记录？还是全局配置？
2. **访问模式是什么**——平时是"只查某一条"，还是要"全量统计 / 遍历"？
3. **保留策略是什么**——留多久？满了怎么办？要不要能手动删？

第 3 条经常被忽略，但它是"数据爆炸"的唯一解药。用户如果说"一直留着"，就要给出封顶手段（见下）。

### 分法：对齐"一次要用哪一整块"

原则：`getData` 一次读一整个文件，所以**分片键应该对齐你每次真正需要的那一块数据**——只查一个人的数据，就别放在需要全量读的文件里。

参考形态（**仅作参考，不要照搬**，具体按上面的三个问题定）：

| 分片键 | 什么时候合适 |
| --- | --- |
| 按 uid 分文件（`{uid}.json`） | 数据主体是用户，每次只关心一个人，数据量随人数增长 |
| 按 groupid 分文件（`{group_id}.json`） | 数据主体是群，群之间互不相干，群内要整体读写 |
| 按单条记录分文件（`{id}.json`） | 记录数量不确定、只增不减，每条独立 |
| 按业务域分子目录 + 单文件 | 数据需要全量扫描（统计、查重、批量遍历），且总量有上限 |
| 不拆，单文件 | 人工配置、全局开关、总量很小的状态 |

反过来说，**如果一个文件已经需要"全量读才能找到一条数据"，而且它还会一直长，就必须拆或封顶。**

### 封顶手段（按需选一种或组合）

- **归档**：提供归档指令，把已结束/过期记录移到 `archive_xxx.json`；
- **分时间**：按月或按周分文件，旧文件整个删掉；
- **过期清理**：数据带时间字段，读取时过滤过期项，并定期真正删除；
- **条数上限**：只保留最近 N 条，超限丢弃最旧的（适合流水、日志类）；
- **手动出口**：提供管理指令，让骰主能主动清空或删除某类数据。

选完要写进代码，而不是停在文档里。**没有清理出口的记录类数据不可交付。**

### 判断文件该不该拆

问三个问题，任意一个答"是"就该拆或封顶：

- 这个文件会**一直变大**吗？（记录类数据几乎都是）
- 它**每次消息都要被读**吗？（高频读 + 大文件 = 最坏组合）
- 它的**键会随群数/用户数线性增长**吗？

经验值：单个 json 控制在**几百 KB 以内**。明显超出说明结构有问题。

### 反例与正例

| 反例 | 问题 | 正例 |
| --- | --- | --- |
| 一个 `data.json` 存配置 + 订单 + 用户 + 日志 | 高频小改动要重写整个大文件 | 配置、订单、用户各一个文件 |
| 订单堆在 `orders.json`，只增不删 | 无上限增长 | 按群或按月分文件 + 归档 |
| 每次消息都 `getData("orders.json")` 读全量 | 读放大，拖慢每条消息 | 按对象分片读取，或内存缓存 + 变更时才写 |
| 配置和运行状态混在一个文件 | 改个开关要重写全部业务数据 | 配置独立，运行时状态独立 |
| 设计时没有"多久删一次"的方案 | 上线三个月后没法收拾 | 设计阶段就定保留策略 |

### 实现细节（用到再抄）

**子目录支持**——标准版 `getData`/`setData` 只拼字符串、不建目录，直接用 `getData("vendors/123.json")` 会报错。在 `setData` 里补两行即可（锁与 `.bak` 逻辑保持不动）：

```python
def setData(filename, data):
    path = f"./plugin/data/{datafile}/"
    full_path = os.path.join(path, filename)
    full_dir = os.path.dirname(full_path)
    if full_dir and not os.path.exists(full_dir):
        os.makedirs(full_dir)          # ← 新增：自动建子目录
    with messagelock:
        ...                            # 其余照旧
```

**删除数据**时要连 `.bak` 一起删，否则残留：

```python
def delete_file(filename):
    path = f"./plugin/data/{datafile}/"
    full_path = os.path.join(path, filename)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
        if os.path.exists(full_path + ".bak"):
            os.remove(full_path + ".bak")
    except Exception:
        pass
```

**遍历分片多文件时的坑**：`.bak` 和数据文件在同一目录，`os.listdir` 会把它们一起列出来，必须过滤：

```python
for f in os.listdir(dir_path):
    if f.endswith(".json") and not f.endswith(".bak"):
        key = f[:-5]
        data = getData(f"{subdir}/{f}")
```

### 与缓存的关系

内存缓存（启动时读一次、之后只在变更时写回）是缓解读放大的常用手段，但要清楚代价：

- 写操作仍要以 `setData` 落盘为准，缓存只是减少读；
- 骰子重启后缓存丢失，要能从文件**完整重建**；
- 多线程下缓存与文件的一致性靠 `messagelock` 保证，不要在锁外改缓存。

## getData / setData（照用，不要"优化"）

```python
messagelock = threading.Lock()


def getData(filename):
    path = f"./plugin/data/{datafile}/"
    if not os.path.exists(path):
        os.makedirs(path)
    with messagelock:
        try:
            with open(path + filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            try:
                with open(path + filename + ".bak", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    shutil.copy(path + filename + ".bak", path + filename)
            except:
                with open(path + filename, "w", encoding="utf-8") as f:
                    pass
        with open(path + filename, "r", encoding="utf-8") as f:
            file = str(f.read())
            if len(file) == 0:
                data = {}
            else:
                data = json.loads(file)
            return data


def setData(filename, data):
    path = f"./plugin/data/{datafile}/"
    with messagelock:
        try:
            with open(path + filename, "r", encoding="utf-8") as f:
                check = json.load(f)
            shutil.copy(path + filename, path + filename + ".bak")
        except:
            pass
        with open(path + filename, "w", encoding="utf-8") as w:
            json.dump(data, w, indent=4, ensure_ascii=False)
```

为什么保持原样：

- 这个实现**不是原子的**，理论上高频读写可能丢数据。但曾经讨论过的替代方案（把锁移到每个读写的调用点、大面积加锁）**会导致青果异常卡死**，实测更糟。
- 现阶段的策略是靠回复词提醒用户操作慢一点（例如秒杀 / 抢购类场景容易并发写同一份数据），并在业务上尽量避免高频并发写同一个文件。
- 每次写入前会把旧内容复制成 `.bak`，读取失败时自动回滚到 `.bak`，已经能兜住大部分意外。

**禁止**：去掉锁、改成 `os.replace` 原子写入、把 `json.dump` 换成别的方式、把 `.bak` 逻辑删掉。这些都属于"看起来更正确但实测更糟"的改动。

## 跨插件读取数据

青果的锁是**按插件隔离**的。两个插件同时读写同一份文件时会丢数据，甚至把文件清空。要跨插件读写，必须让两个插件共用同一把锁：

1. 在**被读方插件 B** 的 `__init__.py` 里声明锁可被跨插件读取：

   ```python
   from . import main
   from <B插件名>.main import pclock
   ```

2. 在**读取方插件 A** 的 `main.py` 顶部导入 B 的锁：

   ```python
   from <B插件名> import pclock as pclock
   ```

3. 在 A 里**另写一套**读写函数（函数名不能叫 `getData` / `setData`，避免和本插件的重名），路径指向 B 的数据目录，并用 B 的锁包裹：

   ```python
   def getArchive(filename):
       path = "./plugin/data/<B插件名>/"
       if not os.path.exists(path):
           os.makedirs(path)
       with pclock:
           ...   # 与 getData 相同逻辑
   ```

注意：

- 先跟用户确认 B 的数据结构。如果 B 的数据是按子文件夹组织的（`getData("engagement", "xxx.json")` 这种），就把 B 的 `getData` / `setData` **原样抄过来改名**，不要自己想当然拼路径。
- 跨插件写数据是高危操作，改之前先问清楚用户是否真的需要写（只读往往就够）。
- **本插件不要把自己的数据目录让别的插件随便写**，除非明确知道对方用哪把锁。

## 定时任务

**不使用 `schedule`**（骰子环境不自带；它本身也是轮询实现，不比标准库可靠，还要额外打包文件 + 两处 import，容易踩包名大小写的坑）。

标准做法：`init` 里启一个守护线程，`while True` 轮询 + 时间戳去重。

```python
from datetime import datetime

PATROL_TIMES = ["12:00", "22:00"]     # 需要触发的时刻
_last_fire_key = None                 # 去重标记
_last_plugin_event = None             # 缓存最近一次消息事件，用于发消息
_scheduler_started = False


def _start_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True
    threading.Thread(target=_scheduler_loop, daemon=True).start()


def _scheduler_loop():
    global _last_fire_key, _last_plugin_event
    while True:
        try:
            now = datetime.now()
            hhmm = now.strftime("%H:%M")
            key = now.strftime("%Y-%m-%d") + " " + hhmm
            if hhmm in PATROL_TIMES and key != _last_fire_key:
                _last_fire_key = key          # 先标记，避免同一分钟内重复触发
                if _last_plugin_event is not None:
                    threading.Thread(
                        target=_do_task, args=(_last_plugin_event,), daemon=True
                    ).start()
        except Exception:
            pass
        time.sleep(30)
```

配套：

```python
class Event(object):
    def init(plugin_event, Proc):
        _start_scheduler()

    def group_message(plugin_event, Proc):
        global _last_plugin_event
        _last_plugin_event = plugin_event
        handle_message(plugin_event, Proc, is_group=True)
```

要点（每一条都是踩过的坑）：

1. **调度线程在 `init` 里启动**，不依赖任何消息，否则没人说话的骰子永远不触发。
2. **`while True` 内部必须有 `try/except`**。循环外抛一次异常，线程就静默死掉，之后完全不再工作，比报错还难查。这里的 `except: pass` 是必要防御，不是过度防御。
3. **用 `key`（日期 + 时分）去重**，否则同一分钟内每轮（30 秒）都会触发一次。
4. **防重入**：`init` 可能被调多次，用 `_scheduler_started` 挡住，否则会起一堆线程。
5. **轮到要发消息时，手上得有 `plugin_event`**（端口、token、骰子 QQ 都在里面）。做法是缓存最近一条消息事件。**冷启动窗口**：骰子刚重启、还没收到任何消息时缓存是 `None`，此时直接跳过本轮（`if _last_plugin_event is not None`）。低流量骰子可能出现"重启后第一次定时任务不触发"，属于已知取舍。
   - 如果不想接受这个取舍，可以用 `Proc.Proc_data['bot_info_dict']`（见 `references/02-events-and-lifecycle.md`）直接拿到账号的 `post_info.port` / `access_token`，走 HTTP API 发消息，完全不依赖消息事件。需要先确认用户是否要这种写法，**不要自作主张改成它**。
6. **任务函数内部也要 `try/except`**，因为它是另一个线程，异常不会冒到消息处理里。
7. 需要"每隔 N 分钟执行一次"而不是固定时刻时，改用 `time.time() - _last_run >= interval` 判断。
