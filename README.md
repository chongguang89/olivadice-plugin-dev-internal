# OlivaDice-Plugin-Dev-Internal

青果骰（OlivaDice / OlivOS / OlivaDiceCore）QQ 机器人插件开发规范 —— 一个给 AI Agent 用的 Skill。

装上之后，你只要正常说需求，Agent 会先按规范问清楚协议端、指令原文、权限、数据、输出、素材来源，再动笔写代码，最后打包成 `.opk`。

目前仅支持 `LLBot` `NapCat` 两种协议的接口及青果原生接口。

建议0基础开发者搜索安装 `WorkBuddy` 使用本skill。
指路：https://www.workbuddy.cn

---

## 安装

### 方式一：下载 zip

仓库页面 → [右侧release](https://github.com/chongguang89/olivadice-plugin-dev-internal/releases/tag/Plugin) → Download ZIP → 直接拖进新建的agent对话框，要求agent安装该skill

装完**新开一个对话**才生效（skill 列表在会话开始时加载）。

### 方式二：要求agent自行安装

新建任务窗口，输入指令“为我安装github上的olivadice-plugin-dev-internal.skill”，安装完毕后新建窗口即可使用。

---

## 验证

新窗口里说一句：

> 帮我写一个青果骰插件

如果 Agent 反问你「骰子挂的是 napcat 还是 LLBot、版本多少」，说明 skill 已经生效。

---

## 里面有什么

```
olivadice-plugin-dev-internal/
├── SKILL.md              主入口：铁律 + 五步工作流 + 索引
├── references/           9 份规范文档 + 2 份接口索引快照
├── templates/            app.json / __init__.py / main.py / README.md
└── scripts/              pack_opk.py（打包）、unpack_opk.py（解包）
```

覆盖的内容：三件套结构、opk 打包、事件与生命周期、消息构造与 API、QQ 风控限速、数据建模与定时任务、图片绘制、代码风格与反模式、协议接口查询、接管已有插件。

该skill亦可接管已有插件，将opk文件后缀改为zip，放入任务窗口并要求使用该skill（自然语言指令：使用olivadice-plugin-dev-internal修改该青果骰插件，要求：xxxxx）即可无缝修改。
注意，如需修改他人插件并传播，务必取得相关二改权限。

---

## 适用范围

- 面向 **Agent 客户端**（WorkBuddy、Claude Code 等支持 skill 的客户端）；网页版 AI 没有 skill 机制，装了也不会生效。
- 协议端支持 **napcat** 与 **LLBot**，两者扩展接口不通用，写代码前会先问清是哪一边。
- 内置接口索引是快照（2026-10-15）。协议端加新接口后索引会查不到，此时 Agent 会停下来要文档——这是设计好的行为，不是故障。

---

## 使用示例

> 帮我写个青果插件：群里发「钓鱼比赛开始」，只有管理员能用，用图片输出

Agent 会走完：确认协议端 → 问清指令原文 / 权限 / 数据 / 输出 / 素材在哪 → 写代码（需要接口时自己查文档，查不到会要你贴参数）→ 自检 → 问能不能上服务器测试 → 打包 `.opk`。

---

## 版权

由 **临皋闲人（QQ：3149790940）** 原创整理。

生成的插件里，署名只出现在 `main.py` 头部注释的末尾（两行紧挨）：

```python
# 本插件由临皋闲人（3149790940）封装的 AI Skill 辅助生成
# 来源：https://github.com/chongguang89/olivadice-plugin-dev-internal
```

`app.json` 的 `author` 归插件作者本人，与本规范无关。
