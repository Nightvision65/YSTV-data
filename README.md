# YSTV 开放赛事数据

激突要塞赛事、选手、阵容、赛果与名次的最终数据，采用 [MIT License](LICENSE)。
身份合并、赛事排除、等级与阵容补充已经应用，直接读取即可使用。
仓库不保存历史核验轮次、合并进度、提取临时文件或审核过程报告。

**修改数据 → 提交并推送到 `main` → 网站自动或由管理员手动同步。**
正常维护不需要 Release、ZIP 包或手工更新文件指纹。

## 目录

```text
YSTV-data/
├── README.md           使用与修改指南
├── LICENSE             MIT 许可
├── dataset.json        最终数据格式标识
├── data/               最终数据，统一英文 snake_case 命名
│   ├── players.json
│   ├── events.json
│   ├── stages.json
│   ├── entrants.json
│   ├── formations.json
│   ├── lineup_members.json
│   ├── encounters.json.gz
│   ├── standings.json
│   ├── records.json
│   ├── sources.json
│   └── source_records.json.gz
└── tools/
    └── dataset.py      校验、解压编辑、同步回仓库及备用 ZIP 导出，无第三方依赖
```

超过 40 MiB 的 JSON 使用 `.json.gz` 保存，解压后仍是 UTF-8 JSON。
`dataset.json` 只记录格式与许可。网站通过 Git 对象校验传输内容，每次固定到一个提交读取整套
数据，并计算数据及评分代码的 SHA256 指纹，避免混用新旧文件。

## 文件与字段

| 文件 | 内容与主要关联字段 |
| --- | --- |
| `players.json` | 最终选手/非选手实体；`player_id`、`name`、`is_player`、`original_names`、`country`/`country_code`；合并后的旧 ID 在 `merged_player_uids` 中用于旧地址跳转。 |
| `events.json` | 已收录赛事；`competition_id`、`name`、`year`、`tier`、日期及分级依据。 |
| `stages.json` | 阶段；`stage_id` → `competition_id`；`players_per_side`/`formations_per_side` 为人数和阵数；`tier`/`honor_tier` 为竞技和荣誉等级。 |
| `entrants.json` | 参赛单位；`entrant_id` → `stage_id`、`player_id`；`roster_formation_ids` 关联实际阵容。 |
| `formations.json` | 阵名、代码与作者；`formation_id` → `entrant_id`、`stage_id`、`player_id`；`name`/`raw_code` 为阵名与完整代码，`work_key` 保留既有统计关联键。 |
| `lineup_members.json` | 已明确的真实多人团队成员，关联阶段和选手；团队成绩不灌入个人 Rating。 |
| `encounters.json.gz` | 交手；`encounter_id` → `stage_id`，双方 `a/b_entrant_id`、`a/b_player_id`，赛果 `outcome`，原件位置 `source`。 |
| `standings.json` | 原件明确的最终名次表；`tables` 保存赛事、阶段、选手/单位、名次区间及证据。完整循环赛推导名次由网站重算。 |
| `records.json` | 直接录入的名次、奖项、晋级、历史官方评选、年度资料覆盖声明；没有 TOP20 或资讯稿件。 |
| `sources.json` | 原件名称、来源 ID、SHA256、表/页信息；没有本机路径或提取工具状态。 |
| `source_records.json.gz` | 已收录阶段的原表内容和坐标，用于查证比赛证据；不是流程日志。 |

文件名 `events.json` 表示赛事，字段 `competition_id` 是该实体的稳定 ID。
`original_names` 是历史原名/别名，用于检索与核对，不新增选手身份。
个人 `1v1`/`3v3`/`5v5` 与真实多人团队分别记录。

## 获取与读取

克隆/Fork 此仓库，或点击 **Code → Download ZIP** 下载当前文件。
直接读取 `data/*.json`；压缩文件可用工具解压到统一 JSON 编辑目录。
以下命令在仓库根目录执行，Python 示例使用 conda `opencode` 环境：

```powershell
conda activate opencode
python tools/dataset.py verify
python tools/dataset.py unpack --destination ../YSTV-data-edit
```

编辑目录必须不存在。例如读取选手名单：

```python
import json
from pathlib import Path
players = json.loads(Path('../YSTV-data-edit/data/players.json').read_text(encoding='utf-8'))
print([p['name'] for p in players if p['is_player']])
```

## 少量文件直接修改

国籍、姓名或赛事等级等小改动，可直接编辑仓库的 JSON，校验后提交并推送。
可以使用 GitHub 网页编辑器或 GitHub Desktop。**只修改 `players.json` 时，不必另外修改
`dataset.json`，也不用重新导出其他数据。**

- 姓名/国籍：修改对应选手；名称和代码保持一致，如 `country: "日本"`、`country_code: "JP"`；未知时两项为 `null`。
- 等级：修改赛事 `tier` 并补充分级依据；涉及阶段时核对 `tier`、`honor_tier`。不足 10 位选手的赛事/阶段等级最高为 C。
- 阵名/代码：修改阵的 `name`/`raw_code`，保留稳定 ID 与既有 `work_key`；网站重新解析单阵和阵容，相关阵容证据一起核对。
- 原表名次：修改 `standings.json` 对应 `entries`；并列 3–4 名使用 `rank_low: 3`、`rank_high: 4`，不编造精确第三名。

保留原表 ID、页/表/格与证据，提交说明列出受影响 ID、位置及依据。
不要提交讨论记录、临时文件、日志、备份或核验进度。

## 压缩文件或多表修改

在解压目录编辑 `data/*.json`，完成后同步回仓库：

```powershell
conda activate opencode
python tools/dataset.py sync --input ../YSTV-data-edit
python tools/dataset.py verify
git diff --stat
git add data dataset.json
git commit -m '更正赛事数据：说明受影响 ID 与依据'
git push origin main
```

`sync` 校验并重新压缩大文件，仅更新内容有变化的文件。编辑前先拉取最新 `main`；不要把过期
编辑目录整套同步回已更新的仓库，覆盖别人的修订。Fork 协作者提交 Pull Request，维护者合并
进 `main` 后网站才同步；其他分支和未合并 PR 不直接上线。

- 赛果：`outcome` 仅用 `a_win`、`b_win`、`draw` 或 `null`。未知赛果不编造，不直接填 Rating、胜率或积分汇总。
- 身份合并：把所有引用改到保留 ID，合并别名，把旧 ID 写入 `merged_player_uids`，再删除被合并者记录。
- 新增赛事：依次增加来源、赛事、阶段、选手/参赛单位、阵、交手和原表名次；引用必须存在，交手双方属于同一阶段。
- 删除赛事：同步删除其阶段、单位、阵、交手、原表记录、名次与关联比赛事实，避免悬空引用。

按实际对战阵数判断赛制，报名提交了几座阵不直接决定赛制。真实换位的两局通过阶段字段
`directional_cells_are_distinct_matches` 声明，网站按每局 0.5 处理，不删除真实换位局来代替去重。
工具校验 ID、引用、名次与赛果格式；身份、证据可信度和等级仍须维护者核对。

## 网站同步与重试

每天香港时间 04:30 左右同步 `main`；管理员后台“赛事数据导入”可以立即拉取。
服务器保留 Git 缓存，后续 `fetch` 增量传输变动对象，固定到一个提交后校验全部关联。
数据或计算规则变化时重算赛事、选手、胜率、荣誉及生涯/年度/累计 Rating，再原子切换公开版。
只改 README 等说明文件时不重算；数据和计算规则相同则复用现有版本。

连接失败每 10 分钟重试，连续失败满 1 小时停止；次日或管理员新触发再尝试。
数据校验失败不自动重试，网站继续提供旧版本。后台记录源提交、结果与下一次重试时间。
**TOP20 和所有资讯都不导入、不重新选评、不改稿。**

## 管理员备用 ZIP

手工上传、离线迁移或保留快照时，从编辑目录导出 ZIP：

```powershell
conda activate opencode
python tools/dataset.py pack --input ../YSTV-data-edit --output ../YSTV-data-backup
```

上传输出目录的 `ystv-data.zip` 到管理员入口。ZIP 内保存逐文件 SHA256 清单。
使用新输出路径，ZIP 和备份目录不用提交 GitHub。

## 许可与来源

整理数据采用 MIT，可复制、修改、再分发和商业使用，保留许可和版权声明。
游戏与第三方原件的权利归各自权利人；仓库不分发原件，不包含运行数据库、账号或资讯。
来源名、SHA256 和坐标供核验，原件由资料维护者保存。
