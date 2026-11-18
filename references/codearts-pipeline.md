# 在华为云 CodeArts 上部署 xhs-optimizer

> 本文档说明本 Skill 如何使用华为云 CodeArts，满足"参赛作品必须使用 CodeArts 或 OfficeAce"的硬性门槛。
> 形态：把"本地一条命令"升级为"在线诊断服务"——创作者上传笔记，流水线自动返回诊断报告。

## 架构

```
创作者 --上传笔记文件--> CodeArts Repo（notes/inbox/ 目录）
                              │
                              ▼ push 自动触发
                       CodeArts Pipeline
                         1. 检出 Skill 代码 + 笔记
                         2. pip install pyyaml
                         3. python3 scripts/optimize.py --note notes/inbox/最新笔记 \
                              --niche $NICHE --keywords $KEYWORDS --output reports/
                         4. （可选）--llm：调用盘古大模型做深度标题改写
                              │
                              ▼
                       产物：reports/诊断报告.md（保留 30 天，创作者下载/截图发小红书）
```

## 配置步骤

### 1. 建仓
- CodeArts Repo 新建代码仓 `xhs-optimizer`，推入本 Skill 全部文件
- 建 `notes/inbox/` 目录作为笔记投递区

### 2. 建流水线
- CodeArts Pipeline → 新建流水线，代码源选上一步的代码仓
- 触发规则：`notes/inbox/` 有 push 即触发（已证实：Push 触发 + `notes/inbox/*` 路径过滤，另含 master 分支过滤）
- 构建步骤（Python 镜像，2026-11-17 实测通过，构建 #20261117.9，59 秒）：
```bash
python3 --version; python3 -m pip --version; which gcc || echo NO_GCC
python3 -m pip install --target="$PWD/.deps" pyyaml || python3 -m pip install --target="$PWD/.deps" --only-binary :all: pyyaml || echo TARGET_INSTALL_FAILED
PYTHONPATH="$PWD/.deps${PYTHONPATH:+:$PYTHONPATH}" python3 -c "import yaml; print('yaml OK', yaml.__version__)"
mkdir -p reports
PYTHONPATH="$PWD/.deps${PYTHONPATH:+:$PYTHONPATH}" python3 scripts/optimize.py --note "$(ls -t notes/inbox/ | head -1 | xargs -I{} echo notes/inbox/{})" --niche "${NICHE:-美食}" --keywords "${KEYWORDS:-}" --output reports/诊断报告.md
```
- `NICHE` / `KEYWORDS` 设为流水线参数，创作者提交时填写（默认值：NICHE=美食，KEYWORDS=空）
- `reports/` 设为构建产物

> 环境说明（2026-11-17 实测）：构建镜像为 Python 3.7.4、pip 18.0、无 gcc、非 root 用户。`pip install pyyaml -q` 原样跑不通：镜像里根本没有 pip 命令，须用 `python3 -m pip`；旧 pip 抓源码包构建失败，须用 `--target="$PWD/.deps"` + `PYTHONPATH` 安装；全新检出的工作区没有 `reports/` 目录，跑脚本前须 `mkdir -p reports`。上面 5 行是已跑通的版本，诊断脚本本身的参数与原方案一致。

### 3. （可选）盘古大模型增强
- 在 CodeArts 流水线变量中配置 `PANGU_API_KEY`（华为云盘古大模型 API Key）
- 构建命令加 `--llm`，对"标题改写建议"一节做深度语义改写（接口层已在 SKILL.md 预留）

## 为什么这样设计
- 创作者侧：不用装 Python，网页上传笔记即得报告——"学一做一晒"闭环里"做"的门槛降到最低
- 传播侧：诊断报告本身就是可晒的内容（"我的笔记被 AI 打了 45 分，改完 82 分"）
- 评审侧：全流程跑在华为云上，CodeArts +（可选）盘古，技术栈真实、可演示

## 验证记录（2026-11-17）
- 流水线“编译部署”第 4 次运行完成（绿），构建 #20261117.9（59 秒，四步全绿）；测试笔记 notes/inbox/测试笔记-减脂餐.txt 推上去自动触发，产物 reports/诊断报告.md 为 45/100（23/8/9/5，先改再发），与本地同一条命令重跑一致。
- 流水线地址：https://devcloud.cn-north-4.huaweicloud.com/cicd/project/fddc24e275b142b29a0530f528fdc423/pipeline/detail/ba22620a7aa04ed4a9a6b3ea9746dd59/0b7ccdf012ab49b7925762734c2897fc?v=1
