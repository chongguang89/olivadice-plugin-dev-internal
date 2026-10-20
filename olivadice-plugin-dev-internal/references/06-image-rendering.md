# 06 图片绘制与分发

## 先搞清楚：这些路径是"骰子端"的，不是"你本机"的

插件里的 `./data/images/`、`./plugin/data/` 都是**相对骰子进程的工作目录**——也就是骰子部署的那台机器（通常是服务器），**不是用户的开发机**。

由此推出三条硬规则：

1. **不要在本地磁盘上搜索 `data/images` 或 `plugin/data` 目录**。找不到是正常的：骰子在服务器上跑，本地根本没有这些路径。
2. **插件读不到用户电脑里的文件**。用户说"文件夹里有 100 张图，帮我发出去"，指的是**服务器上**的某个目录，不是他电脑桌面上的那个。
3. **要处理已有的图片/文件，必须先让它们落到骰子能读的地方**（`data/images/<插件名>/`），这是前置条件，不是插件能自己解决的事。

遇到这类需求，**先停下来问清楚**，别动手搜本地：

- 图片现在在哪？在你电脑上，还是已经传到服务器了？
- 一共多少张？多大？什么格式？
- 文件名有没有规律（决定按什么顺序发）？

然后告诉用户正确的操作方式：**把图片上传到服务器的 `<骰子根目录>/data/images/<插件名>/<子目录>/` 下**，插件只负责按文件名读和发。如果用户不会传，就说明"这一步必须你来，插件没法访问你的电脑"。

## 存放位置（硬规则）

图片**只能**放在与 `plugin/` 同级的 `data/images/` 下，按文件名调取：

```
<骰子根目录>/
├── plugin/
│   └── data/<插件名>/xxx.json      ← JSON 数据放这里
└── data/
    └── images/<插件名>/xxx.png     ← 图片放这里（注意 images 是复数）
```

- 插件自己的图片放在 `./data/images/<插件名>/` 下；需要分组时再建子目录（例如 `./data/images/<插件名>/二维码/`）。
- **不要**把图片放进插件文件夹，也不要把图片打进 opk。
- 目录不存在时自己建：

  ```python
  img_dir = f"./data/images/{datafile}/"
  if not os.path.exists(img_dir):
      os.makedirs(img_dir, exist_ok=True)
  ```

## 发送图片

```python
# 直发：file= 填相对 ./data/images/ 的路径，不带 data/images 前缀，不带 file://
plugin_event.reply(f"结果如下：\n[CQ:image,file={datafile}/qr.png]")

# 也可以走 send 主动发到别的群
plugin_event.send("group", groupid, f"[CQ:image,file={datafile}/xxx.png]")

# 放在合并转发节点里：file= 填 file:// 绝对路径
{"type": "image", "data": {"file": f"file://{os.path.abspath(img_path)}"}}
```

两种写法不能混用：直发用相对路径，合并转发用 `file://` 绝对路径。

## 字体

**不要自带字体文件**，直接用系统默认黑体。写一个加载函数，按候选路径依次尝试，最后兜底：

```python
FONT_CANDIDATES = [
    "C:/Windows/Fonts/simhei.ttf",          # 黑体
    "C:/Windows/Fonts/msyh.ttc",            # 微软雅黑
    "C:/Windows/Fonts/simsun.ttc",          # 宋体
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()
```

骰主环境一般是 Windows（`OlivaDice-OlivOS-Win`），所以 Windows 字体路径排在前面。加载失败必须能兜底，否则一张图都画不出来。

## 用 PIL 画图

`Pillow` 骰子环境自带，可以直接用：

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.new("RGB", (width, height), "#FFFFFF")
draw = ImageDraw.Draw(img)
font = load_font(24)
draw.text((x, y), "文本", fill="#333333", font=font)
draw.rectangle([x0, y0, x1, y1], fill="#F2F2F2")
img.save(save_path)
```

注意：

- 文字用 `draw.textlength(...)` 量宽度来布局，不要按字符数硬算。
- 中文长文本自己折行。
- 画完先存文件，再发送。
- 绘制整体包 `try/except`，失败时 `reply` 告知用户，不要静默。

## 大量发送

一次要发几十上百张图、单条塞多张、或者要长时间高频发送时，1~3 秒的常规间隔不够用。判断标准与处理方式见 `references/04-risk-control.md` 的「1~3 秒覆盖不住的情况」——**不要自己拍一个间隔写进代码**，先提示风险、再问用户希望每隔多少秒发一条。

## 渲染缓存

同样的图不要每次请求都重画。做法是记录数据与图片的更新时间戳，只有在数据比图片新时才重新渲染：

```python
meta = getData("meta.json")
need_render = meta.get("image_update", 0) < meta.get("data_update", 0)
if need_render:
    render_image()
    meta["image_update"] = time.time()
    setData("meta.json", meta)
```

这属于按需优化，业务简单（画一张就不变的图）时也可以不做。

## 可选：图片清理

如果插件会持续生成图片，可以加一个"只保留最近 N 个文件"的清理逻辑；没有明确需求就不要自作主张删文件。
