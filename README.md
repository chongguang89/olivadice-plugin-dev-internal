# 青果骰插件开发 Skill · 分发说明

> 给分享者看的一份说明。产物：GitHub 仓库（推荐）或 `olivadice-plugin-dev-internal.zip`
> 整理：临皋闲人（3149790940）

---

## 一、发给谁

**只发给用「支持 skill 的 agent」的人**——WorkBuddy、Claude Code 之类的客户端。这类工具能读取并加载 skill。

网页版 AI（DeepSeek、豆包、Kimi 网页版）不用管：没有 skill 机制，给了也不会生效。

---

## 二、GitHub 分发（推荐）

### 1. 推仓库

仓库根目录**就是 skill 本体**（`SKILL.md` 直接躺在根上），仓库名与 skill 名一致：`olivadice-plugin-dev-internal`。

```bash
cd olivadice-plugin-dev-internal
git init
git add .
git commit -m "init: olivadice-plugin-dev-internal skill"
git branch -M main
git remote add origin https://github.com/<你的用户名>/olivadice-plugin-dev-internal.git
git push -u origin main
```

仓库结构（推之前对一眼）：

```
olivadice-plugin-dev-internal/
├── SKILL.md           ← 入口，文件名不能改
├── README.md          ← 仓库首页的安装说明（给人看，不影响 skill 加载）
├── .gitignore
├── references/
├── templates/
└── scripts/
```

**不要推**：`.DS_Store`、`__pycache__/`、`*.pyc`、任何 `.opk`、你自己的测试插件。`.gitignore` 已经挡掉了。

### 2. 发什么给用户

就一个地址 + 一句话：

> 地址：`https://github.com/<你的用户名>/olivadice-plugin-dev-internal`
>
> 话术（连地址一起发）：
> 「从这个地址安装青果骰插件开发 skill，放到 `~/.workbuddy/skills/olivadice-plugin-dev-internal/`，装完确认 `SKILL.md` 在根目录。」

Agent 收到后会用 `git clone` 或 `curl` 把仓库拉下来放进 skills 目录 —— 这属于常规文件操作，能做。

### 3. 说实话：能不能「给个网址就自动装」

**能，但要带一句明确的安装要求，不是纯 URL 就自动生效。**

- WorkBuddy 内置的「一句话装 skill」走的是**官方 marketplace 搜索安装**，不认任意 GitHub 地址；
- 但只要用户说清「装到哪里」，agent 就会用 shell 下载 —— 这一步是通用的；
- 装完必须**新开一个对话**，skill 列表才重新加载。

想更省事可以发版时顺手传一个 release 附件 zip，给国内用户备用（GitHub 直连有时不稳）：

```bash
curl -L https://github.com/<你的用户名>/olivadice-plugin-dev-internal/archive/refs/heads/main.zip -o /tmp/s.zip
unzip -q /tmp/s.zip -d /tmp/s
mv /tmp/s/olivadice-plugin-dev-internal-main ~/.workbuddy/skills/olivadice-plugin-dev-internal
```

---

## 三、手动安装（对方不会用 agent 时）

1. 仓库页面 → Code → Download ZIP，或直接用 `dist/olivadice-plugin-dev-internal.zip`；
2. 解压得到 `olivadice-plugin-dev-internal` 文件夹（如果名字带 `-main`，改回 `olivadice-plugin-dev-internal`）；
3. 整个文件夹放进：
   - **WorkBuddy**：Windows `C:\Users\<用户名>\.workbuddy\skills\`，macOS `~/.workbuddy/skills/`
   - **其他客户端**：`~/.<客户端名>/skills/`，以它自己的文档为准
4. 重启客户端或新开对话。

要点：**文件夹名与结构不要改，`SKILL.md` 必须叫这个名字**；一个 skills 目录可放多个 skill，互不冲突；不想要了直接删文件夹。

---

## 四、验证是否生效

新窗口说一句：

> 帮我写一个青果骰插件

Agent 反问你「骰子挂的是 napcat 还是 LLBot、版本多少」→ 生效了。

没反问你协议端、直接开始写代码 → 没加载上，检查目录层级（是不是套了两层文件夹、`SKILL.md` 是否在根）。

---

## 五、生效后是什么体验

对方什么都不用记，正常说需求：

> 帮我写个青果插件：群里发「查排单」返回当前未完成的单子，只有管理员能用，用图片输出

Agent 会自己走：确认协议端 → 问清指令原文 / 格式（固定文本还是 `.` 前缀）/ 权限 / 数据 / 输出 / 素材在哪 → 写代码（需要接口时自己去查文档，查不到会停下来要参数）→ 自检 → **问能不能上服务器测试、问 `app.json` 作者署名** → 打包 `.opk`。

设计上写死了「任何有疑惑或触碰边界的步骤都必须停下提问」，所以不会瞎猜。

---

## 六、怎么跟 AI 要接口文档

AI 说某个接口查不到时，让它照下面三样要（对方从文档站复制即可）：

1. **Body 参数**（接口详情页中间的表格）
2. **请求示例代码**（切到 Python 页签，代码块右上角一键复制）
3. **返回成功响应**（页面最下方示例）

接口页右上角有「复制页面」按钮，整页复制也行。

---

## 七、你需要维护的部分

- **接口索引会过期**。内置两份快照是 2026-10-15 的（`references/api-index-*.md`）。协议端加新接口后查不到，AI 会停下来要文档——这是设计好的行为，不是故障。
- 更新方式：从协议文档站重新导出索引 → 替换两个文件 → 提交 → 发个 tag `v1.1`。
- 建议每次发版在 `SKILL.md`「版权」一节下记一行版本日期，方便用户判断新旧。

---

## 八、包里有什么（可公开核验）

```
olivadice-plugin-dev-internal/
├── SKILL.md                 主入口：铁律 + 工作流 + 索引
├── README.md                仓库首页安装说明
├── references/              9 份规范文档 + 2 份接口索引快照
├── templates/               app.json / __init__.py / main.py / README.md
└── scripts/                 pack_opk.py（打包）、unpack_opk.py（解包）
```

- `templates/main.py` 是**通用模版**，不含任何私有插件的业务逻辑；
- 规范里的路径、文案均为通用示例，不含具体项目的真实数据；
- 署名只出现在**生成的 `main.py` 头部注释最后一行**（`# 本插件由临皋闲人（3149790940）封装的 AI Skill 辅助生成`），不会写进代码正文或 `app.json`；`app.json` 的 `author` 由使用者自己决定。
