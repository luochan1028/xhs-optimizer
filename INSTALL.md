# 别人怎么用 xhs-optimizer

这个 Skill 的版本是 v1.0.0，和小红书 Skill 市场上的 xhs-zhenduan、华为云 Skill 门户上的 xhs-optimizer 是同一版，诊断逻辑完全一致。下面三种方式都能跑通，选一种就行。

## 方式一：本地运行（推荐，离线、零成本）

环境：Python 3.8+，装一个依赖：

```bash
pip install pyyaml
```

下载：在 CodeArts 代码仓 xhs-optimizer 里下载 zip（或克隆），进到 `xhs-optimizer` 目录。

仓库地址：https://devcloud.cn-north-4.huaweicloud.com/codehub/project/fddc24e275b142b29a0530f528fdc423/codehub/3120806/home?ref=master

克隆地址：https://codehub.devcloud.cn-north-4.huaweicloud.com/fddc24e275b142b29a0530f528fdc423/xhs-optimizer.git

> 注意：仓库已公开，所有访客只读，不用登录就能查看和下载。

笔记文件：新建一个 `.txt`，第一行是标题，空一行，后面是正文，标签直接写在正文里（例如 `#求职`）。

运行：

```bash
python3 scripts/optimize.py --note 笔记.txt --niche 职场 --keywords 简历,HR,面试 --output 诊断报告.md
```

跑完在 `--output` 指定的位置得到一份 Markdown 诊断报告：综合评分（0–100）+ 四维分数 + 逐项诊断 + 3 个标题改写建议 + 标签推荐 + 发布时间建议。

常用参数：`--niche` 是垂类（美妆 / 美食 / 职场 / 学习 / 搞钱 / 穿搭 / 旅行 / 家居 / 母婴 / 数码），决定标签推荐用哪个池子；`--keywords` 是核心关键词，标题改写会拿它们去套句式；`--cover` 传封面图会多一项封面初检（3:4 竖版最佳，不计入总分）；`--card` 会同时生成一张 HTML 诊断卡片，浏览器打开截图就能发小红书；`--style` 传一篇对标爆款笔记（第一行是标题），会拆它的钩子结构再套你的关键词。

## 方式二：装进你的 Agent

如果你用 Claude Code、Codex 或其他支持 Agent Skills 的工具，把整个 `xhs-optimizer` 目录放进 Agent 的 skills 目录（例如 `~/.claude/skills/xhs-optimizer/`，具体位置以你所用工具的文档为准），重启 Agent，就能在对话里直接调用它。

`SKILL.md` 顶部带标准 frontmatter（`name` / `description`），符合 Agent Skills 格式。

## 方式三：在线试用

在线试用页（与本地版同一套评分规则，浏览器里直接跑）：

http://119.3.227.184:8082/trial.html

## 验证一下：跑通了没有

用包里自带的示例跑一遍，应该得到 45/100，和 `examples/sample_report.md` 一致：

```bash
python3 scripts/optimize.py --note examples/sample_note.txt --niche 美食 --keywords 减脂餐,30天,8斤 --output /tmp/我的诊断.md
```

## 分数怎么读

- ≥ 80：优秀，直接发
- 60–79：可发，建议按报告里的逐项问题改一遍再发
- < 60：先改再发

风险词库是示例版，命中不等于定罪，请人工复核（比如“第一个错误”会命中风险词“第一”，换成 ①②③ 就不命中了）。

## 想自己改规则

见 `SKILL.md` 的“自定义”一节：加垂类改 `data/tags.yaml`，加标题句式改 `data/title_patterns.yaml`，加风险词改 `data/risk_words.txt`，调评分权重改 `scripts/optimize.py` 里各 `diagnose_*` 的分值。
