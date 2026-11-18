# 参赛作品：xhs-optimizer —— 小红书爆款笔记诊断优化 Skill

> 在线试用：http://119.3.227.184:8082/trial.html（浏览器直接跑，不用装）
> 实测：简历笔记 46 分改到 90 分，只改了 5 处（见 manual-demo/）
> 本地跑：`pip install pyyaml`，然后 `python3 scripts/optimize.py --note 笔记.txt --niche 职场 --keywords 简历,HR,面试`

## 一、创意说明

小红书有亿级创作者，但大多数人的笔记死在三件事上：标题没人点、标签没曝光、踩了限流词自己还不知道。
xhs-optimizer 是一个**发前诊断 Skill**：把"爆款笔记的方法论"沉淀成可复用的规则库（标题句式库、风险词库、垂类标签库、发布时间表），
输入一篇笔记，输出四维评分 + 可执行的优化建议。创作者"学一做一晒"：学方法、用 Skill 诊断、晒"46分改到90分"的过程（实测）——
诊断报告本身就是一篇天然的小红书笔记。

## 二、为什么是这个题（环境分析）

1. **受众规模**：上一版"C语言作业批改"的受众是几万高校教师，在小红书信息流里是死内容。本版受众是**全体小红书创作者**，传播天花板完全不同。
2. **双重评审**：华为评委看技术（CodeArts + 盘古，见第五节），小红书评委看传播（真实用户反馈）。本作品两边都给东西。
3. **赛道灵魂"学一做一晒"**：诊断→优化→晒分，这个闭环是内生的——用户用了涨粉，会自发回来晒，形成病毒传播。
4. **可晒性**：输出的诊断报告（评分、四维雷达、改写前后对比）截图即笔记素材。
5. **主场优势**：小红书联办的赛道，为小红书生态本身做的 Skill，天然对题。

## 三、真实场景

- 示例笔记（`examples/sample_note.txt`）是一篇真实的"平庸笔记"形态：标题平淡、无分段、零 emoji、
  1 个标签、含"私聊我/加微信"限流词——新手创作者的典型死法，诊断打 45 分，每条问题精准命中
- 规则库来自公开的内容方法论总结 + 创作者社区经验，可持续扩展

## 四、可运行（已实测）

- 本机实测：`pip install pyyaml` 后一条命令出报告（见 `examples/sample_report.md`）
- 默认纯规则运行，零成本、离线可跑；`--llm` 预留盘古大模型增强位
- 风险词库明确标注"示例版、命中请人工复核"，不夸大能力边界

## 五、华为云使用（满足参赛硬性门槛）

- **CodeArts**：代码仓 xhs-optimizer 已建（华北-北京四，项目 ID fddc24e275b142b29a0530f528fdc423，仓库 ID 3120806），地址 https://devcloud.cn-north-4.huaweicloud.com/codehub/project/fddc24e275b142b29a0530f528fdc423/codehub/3120806/home?ref=master ；部署方案见 `references/codearts-pipeline.md`（Pipeline“上传笔记→自动诊断→报告回传”在线服务，方案已写、尚未部署）
- **盘古大模型**（可选增强）：`--llm` 位用于深度标题语义改写，API Key 配在流水线变量中

## 六、可复用

- 加垂类/加句式/加风险词：各改一个数据文件即可，零代码改动
- 评分权重、诊断阈值集中在 `optimize.py` 顶部函数，一目了然
- 不绑定任何账号体系，个人创作者、MCN、代运营拿去即用

## 七、原创声明

本作品（含诊断引擎、标题句式库、风险词库、标签库、CodeArts 部署方案及全部示例）为参赛者原创，
方法论为自行总结，未抄袭、未基于他人作品改编。

## 八、文件结构

```
xhs-optimizer/
├── SKILL.md                  # Skill 定义
├── scripts/
│   ├── optimize.py           # 诊断引擎（已实测，支持 --cover/--card）
│   └── check_pack.py         # 提交前合规自检（≤30文件/40MB）
├── data/
│   ├── title_patterns.yaml   # 高点击标题句式库
│   ├── risk_words.txt        # 风险词库（示例版）
│   ├── tags.yaml             # 垂类标签库（10垂类）
│   └── post_times.yaml       # 发布时间建议
├── references/
│   └── codearts-pipeline.md  # CodeArts 在线部署方案
├── examples/
│   ├── sample_note.txt       # 示例输入（45分平庸笔记）
│   └── sample_report.md      # 实测输出
└── README.md                 # 本文件
```

> 注：`~/workspace/competition-skill/c-grader/`（上一版C语言批改）保留为个人教学工具，不作为本次参赛作品。
