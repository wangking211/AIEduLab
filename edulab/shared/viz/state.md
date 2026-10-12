# 共享状态与补丁契约（给 agent 用）

书页是**运行时**，文件系统是**持久化**，JSON 是**线上格式**。三者合起来让「书」与「对话」
操作同一份 spec——这就是共享状态层。

```
                 ┌─────────────────────────────────────────┐
   AI 对话  ──→  │  补丁 JSON（路径寻址的局部修改）           │
                 └────────────────┬────────────────────────┘
                                  │  validate（不通过就拒绝）
                                  ▼
   书页（运行时）  ←──  overrides.json（已入库的改动，随书分发）
        ▲                          ▲
        └── localStorage 本地草稿 ──┘（用户/agent 试改，未入库）
```

---

## 一、三层状态（优先级从低到高）

| 层 | 存放 | 谁写 | 语义 |
|---|---|---|---|
| **原始 spec** | `figures.py` | 作者 | 书稿的基线 |
| **overrides.json** | 与书页同目录 | `patch.py`（**经校验**） | **已入库的改动**，随书分发，读者看到的就是它 |
| **本地草稿** | `localStorage` | 书页里的「应用补丁」 | 试改，只在本人浏览器里，可一键还原 |

书页启动时**依次叠加**：原始 → overrides → 草稿。所以本地草稿永远覆盖已入库的改动。

> **区分很重要**：已入库的改动**不显示**「本地草稿」标记；用户自己试改的才显示。

---

## 二、导出状态（书页 → agent）

书页右下角「状态 / 交给 AI」→「导出状态」，得到：

```jsonc
{
  "kind": "edu-book-state", "version": 1,
  "book": "数学思想：从计数到无穷",
  "chapter": "ch01", "chapterTitle": "数：从计数到无穷",
  "viewing": [ { "figure": "fig-crisis", "step": 4, "steps": 6 } ],   // 读者正在看哪一步
  "figures": { "fig-crisis": { /* 完整 spec（已含 overrides 与草稿）*/ } },
  "selection": "读者选中的文本",       // 有了它才能做「解释这句」
  "scroll": 0.42,                      // 阅读进度
  "draft": { }                         // 本地草稿
}
```

**给 agent 的要点**：拿到 `figures[<id>]` 就有了完整上下文，可以据此产出**精准的局部补丁**；
`viewing` 告诉你读者卡在哪一步——**优先改他正在看的那张图**。

---

## 三、补丁格式

```jsonc
{
  "kind": "edu-viz-patch", "version": 1,
  "book": "数学思想：从计数到无穷", "chapter": "ch01",
  "patches": [
    {
      "figure": "fig-crisis",
      "note": "给每次扩张补上「代价」",          // 一句话说清改了什么
      "ops": [
        { "path": "layers/0/text", "value": "新标题" },
        { "path": "layers", "op": "append", "value": { /* 新图层 */ } },
        { "path": "layers/5", "op": "delete" },
        { "path": "layers/2/data/0/label", "value": "改卡片标题" }
      ]
    }
  ]
}
```

### 路径语义（两侧实现完全一致）

- `/` 分隔；**数字段是数组下标**（`layers/3/data/0/label`）。
- `op: "set"`（默认）：改值；不存在会报错。
- `op: "append"`：往数组末尾追加。
- `op: "delete"`：删除该下标/字段。
- 也可整图替换：`{ "figure": "...", "spec": { /* 全量 spec */ } }`。

> **同图多条补丁的合并规则**：书页（`importPatch`）与 `patch.py` 都会**拼接 ops**，不是覆盖。

---

## 四、应用补丁

### 在书页里（试改）

```js
BookState.importPatch(patchJson);   // → { ok, applied:[...], failed:[...] }
BookState.exportState();            // 见第二节
BookState.exportDraft();            // 把本地草稿导成一份补丁（拿去入库）
BookState.reset();                  // 清空本地草稿，回到 overrides + 原始
```

试算失败**不落地**：先对 `specOf(id)` 试算一遍，抛错就跳过该图并在 `failed` 里报告。

### 在命令行（入库）

```bash
python patch.py <patch.json> [...]     # 校验 → 写入 output/overrides.json
python patch.py --list                 # 看当前有哪些改动
python patch.py --clear                # 清空
```

**整批拒绝**：只要有一张图没通过校验，**整批不写入**，书稿保持原样（避免半成品污染）。

---

## 五、质量闸门（为什么敢让 agent 改图）

补丁在落盘前会跑 `vizkit.validate`，以下任一都会导致**拒绝**：

| 码 | 含义 | agent 该怎么改 |
|---|---|---|
| E1 | view 非法 | 检查 `xRange`/`yRange` 是否递增 |
| E2 | 未知图元 | 查 `grammar.md` 的图元清单 |
| E3 | 必填字段缺失 / 字段名拼错 | 按 report 里的字段名修正 |
| E4 | 表达式引用了未定义变量 | 变量必须在 `params`/`scalars`/`steps` 里 |
| E5 | 坐标越界 | 收窄图元或放宽 `view` |
| E6 | 文本溢出画布 | 缩短 / `\n` 折行 / 改对齐 |
| W1 | 文本互相遮挡 | 上下分层或错开 x |
| W2 | 方块类没开 `equalAspect` | `spec(..., equal_aspect=True)` |
| W3 | 步骤缺 `note` | 每步写一句 note |

report 里每条错误都带 `↳ 修法`，**照着改再交一次**即可。

---

## 六、agent 的标准工作流

**A. 入库链路**（改完所有人下次打开都生效）

```
1. 读 grammar.md（写图）与 state.md（改图）
2. 拿「书页导出的状态」→ 知道读者在看什么、图的完整 spec
3. 产出补丁（ops 尽量小而准，别整图重写）
4. python patch.py patch.json        ← 校验；不通过就按 ↳ 修法改
5. 通过 → overrides.json 入库 → 书页下次打开即生效
```

**B. 实时链路**（读者正看着，要立刻生效）

```
1. python bridge.py asks             ← 看待回答的问题
2. python bridge.py show <id>        ← 读者看到第几步、选中了什么、图的完整 spec
3. Python 算几何 → 产出补丁
   · 修订自己上一次的改动 → 加 "replace": true
4. python bridge.py reply <id> --patch p.json --say "回答"
   ← 同样先校验；不过就整批拒绝，页面不会动
5. 书页 SSE 收到 → 重画图 + 显示回答（不刷新）
```

**三条纪律**：

1. **优先局部改**：能用 3 条 `ops` 解决就别整图替换——整图替换会丢掉别人后来的改动。
2. **每条补丁写 `note`**：入库后 `--list` 会显示它，是给人看的变更记录。
3. **改完自证**：`python check.py` 应仍为 0 错误 0 警告；实时链路里则看页面有没有重画成功。

---

## 七、实时通道（bridge.py）

`bridge.py` 是书页与 agent 之间的**本地桥**，纯标准库、零依赖。它同时干两件事：

1. **静态服务器**：服务书稿 `output/` 目录——书页照常离线可开；
2. **实时通道**：书页提问 → agent 改图 → 书页**不刷新就跟着变**。

桥不在时书页**自动降级为纯离线阅读**，不报错。

### 启动

```bash
python bridge.py serve --port 8810        # 默认服务 books/math-thought/output
python bridge.py serve --dir <书稿目录>   # 换一本书
```

### 协议（全部 JSON，同源，无 CORS）

| 方法 | 路径 | 作用 |
|------|------|------|
| POST | `/api/ask` | 书页提问 `{figure, question, state}` → `{id}` |
| GET | `/api/patches?since=N` | 书页拉补丁（轮询或启动时重放） |
| GET | `/api/events?since=N` | SSE 长连接，有补丁立即推 |
| POST | `/api/patch` | agent 推补丁，**先校验，不通过则 400** |
| GET | `/api/status` | `{asks, pending, patches}` |

### agent 侧 CLI（与 HTTP 等价）

```bash
python bridge.py asks                          # 看待回答的问题
python bridge.py show ask_xxxxx                 # 看问题 + 读者当时看到第几步、选中了什么
python bridge.py reply ask_xxxxx --patch p.json --say "回答文字"
python bridge.py reply --figure fig-complex --ops '[{"path":"/layers/0/label","value":"x"}]'
python bridge.py log                           # 看已推的补丁
```

### 补丁的两种叠加语义

- **默认：追加**。多次回答依次拼接 `ops`，适合"再补一点"。
- **`"replace": true`：替换**。重置该图的实时叠加，只保留本次 `ops`。
  **修订自己的上一次改动时必须用它**，否则内容会翻倍。

入库（`patch.py`）那条链路另有一层**幂等**：每份补丁存内容签名 `sigs`，
同一份补丁重复应用会被识别并跳过，不会把 `ops` 翻倍。

### 叠加次序（书页）

```
原始 spec → overrides.json（已入库） → LIVE（AI 实时改的） → drafts（读者本地试改）
```

LIVE 不落盘，每次开页从 `_live/patches.jsonl` **重放**，所以是可复现的。

### 数据落盘

- `<书稿>/_live/asks.jsonl` —— 读者的提问（append-only，纯文本，可 git diff）
- `<书稿>/_live/patches.jsonl` —— agent 推过的补丁日志（含 `replace` 标记）
- `<书稿>/output/overrides.json` —— 已入库的改动（`patch.py` 写，书页启动载入）

### 为什么要一层校验

书页是读者的**运行时**，文件系统是**持久化**，JSON 是**线上格式**。
三者之间如果直接互写，一个错下标就会让整页白屏。所以：

- 书页提问时把完整 state 一起带上（含图的 spec、读者看到第几步、选中了什么）；
- agent 不手写 JSON，用 Python 算几何 → 产出补丁；
- **入库前和推送前都过同一套校验器**，不过就整批拒绝，书稿/页面都不动。

---

## 八、这条路径还能长成什么

现在做到的是「**双向 + 可入库 + 实时**」：读者在书里问 → agent 看到上下文 →
改的不是副本而是他正看的那张图 → 书页秒级跟着变；满意的改动再 `patch.py` 入库。

往前一步：

- **写作流水线**：大纲 YAML → 批量词条 → 生成 → 审计 → 装配成书；
- **多本书 / 多读者**：`_live/` 按图分区已就绪，可扩展成按会话隔离；
- **浏览器书签工具**：`navigator.clipboard` 导出状态 + 剪贴板桥，桥未启动时也能传。
