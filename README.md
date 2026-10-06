# YSTV 开放赛事数据

激突要塞赛事、选手、阵容、赛果与名次的最终数据，采用 [MIT License](LICENSE)。
身份合并、赛事排除、等级与阵容补充已经应用到数据中，无需重放历史核验过程。
仓库不保存轮次计划、合并进度、提取临时文件、审核过程报告、TOP20、资讯或运行数据库。

## 目录与内容

```text
YSTV-data/
├── README.md           使用、修改与发布指南
├── LICENSE             MIT 许可
├── dataset.json        格式、版本、文件清单与 SHA256
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
    └── dataset.py      校验、解包、打包与发布 manifest 工具，无第三方依赖
```

超过 40 MiB 的 JSON 以 `.json.gz` 储存；格式仍是 UTF-8 JSON 数组，用工具解压即可编辑。
`dataset.json` 的 `files` 同时记录逻辑文件名、仓库存储文件名、解压后的大小和 SHA256。
发布包保存相同的最终数据，ZIP 内 `package.json` 是运输校验清单。

| 文件 | 内容与主要关联字段 |
| --- | --- |
| `players.json` | 最终选手/非选手实体；`player_id`、`name`、`is_player`、`original_names`、`country_code`。合并后的旧 ID 留在 `merged_player_uids`，用于旧地址跳转。 |
| `events.json` | 已收录赛事；`competition_id`、`name`、`year`、`tier`、日期及分级依据。 |
| `stages.json` | 赛事阶段与实际赛制；`stage_id` → `competition_id`；`players_per_side` 与 `formations_per_side` 分别表示人数、阵数，`tier` 与 `honor_tier` 分别表示竞技等级、荣誉等级。 |
| `entrants.json` | 阶段参赛单位；`entrant_id` → `stage_id`、`player_id`。真实多人团队不会当作一个作者的个人赛果。 |
| `formations.json` | 最终阵名、代码与作者；`formation_id` → `entrant_id`、`stage_id`、`player_id`。`roster_formation_ids` 位于参赛单位，关联实际使用阵容。 |
| `lineup_members.json` | 已明确的真实多人团队成员，关联阶段与选手；不把团队成绩灌入个人 Rating。 |
| `encounters.json.gz` | 最终交手；`encounter_id` → `stage_id`，双方 `a/b_entrant_id`、`a/b_player_id`，赛果 `outcome`，来源 `source`。 |
| `standings.json` | 原件明确记载的最终名次表；`tables` 含赛事、阶段、参赛单位/选手、名次区间和证据。完整循环赛推导名次由网站依据交手重算。 |
| `records.json` | 当前生效的其他比赛事实：直接录入的名次、奖项、晋级、历史官方评选及年度资料覆盖声明；不包含编辑评选稿件。 |
| `sources.json` | 原件名、来源 ID、SHA256 和表/页信息；无本机绝对路径或提取工具状态。 |
| `source_records.json.gz` | 已收录阶段的原表记录与坐标，供查询比赛证据；这是资料内容，不是流程日志。 |

## 下载与读取

只想使用数据：到 [最新正式版本](https://github.com/Nightvision65/YSTV-data/releases/latest)
下载 `ystv-data.zip` 与 `ystv-data-manifest.json`，解压后读取 `data/*.json`。
manifest 中的 SHA256 应与 ZIP 文件一致；包内清单用于逐文件检查。

需要协作修改：Fork/克隆此仓库。以下命令在仓库根目录运行，Python 示例使用 conda `opencode` 环境。

```powershell
conda activate opencode
python tools/dataset.py verify
python tools/dataset.py unpack --destination ../YSTV-data-edit
```

第二条命令核对全部文件指纹、ID 与关联，第三条在新的目录中生成未压缩的最终数据。
例如读取选手名单：

```python
import json
from pathlib import Path
players = json.loads(Path('../YSTV-data-edit/data/players.json').read_text(encoding='utf-8'))
print([p['name'] for p in players if p['is_player']])
```

## 如何修改

在解包目录编辑 `data/*.json`，保留现有字段与稳定 ID。修改依据应附在对应记录的 `source`、
`evidence` 或分级 `classification` 中；提交说明列出受影响 ID、原表位置与修改理由。
不要把讨论记录、临时文件、备份、校验日志或工作进度提交到仓库。

- 更正姓名或国籍：修改 `players.json` 对应记录。国籍名称和代码保持一致，例如 `country: "日本"`、`country_code: "JP"`；未知时两项为 `null`。身份合并需把被合并者的所有引用改到保留 ID，别名合并，旧 ID 写入 `merged_player_uids`，最后删除被合并者记录。
- 更正赛事等级：修改 `events.json` 的 `tier` 并记录分级依据。涉及阶段等级/荣誉时同步核对 `stages.json` 的 `tier`、`honor_tier`；不足 10 位选手的个人赛事/阶段等级最高为 C。
- 更正赛果：修改 `encounters.json` 的 `outcome`，只用 `a_win`、`b_win`、`draw` 或 `null`。未知赛果不编造；保留来源 ID、页/表/格等证据。不要直接填 Rating、胜率或积分汇总，网站会重算。
- 更正原表名次：修改 `standings.json` 的对应 `entries`。并列 3–4 名使用 `rank_low: 3`、`rank_high: 4`，不拆成虚构的精确第三名。推导的循环赛名次无需手改，修改交手后网站重新计算。
- 新增赛事：先增加来源和赛事，再录入阶段、选手/参赛单位、阵与交手，最后录入原表名次。先确保引用都指向存在的 ID，且交手双方属于同一阶段。
- 删除赛事：同时删除其阶段、参赛单位、阵、交手、原表记录、名次与关联比赛事实；不要留下悬空引用。

原有数据采用稳定的 `competition_id`/`stage_id`/`player_id` 字段；文件名 `events.json`
表示赛事，`competition_id` 是同一实体的 ID。`1v1`/`3v3`/`5v5` 按实际对战阵数判断，
报名提交了几座阵不直接决定赛制。换位的两局使用阶段的 `directional_cells_are_distinct_matches`
声明，网站按每局 0.5 处理；不要以删除真实换位局代替去重。

## 校验、提交与发布

编辑完成后，生成新的仓库内容与正式附件。输出目录必须不存在：

```powershell
conda activate opencode
python tools/dataset.py pack --input ../YSTV-data-edit --output ../YSTV-data-v2026.10.07 --version v2026.10.07
```

工具核对 ID/引用与赛果，重建 `dataset.json` 指纹，在输出目录生成 `repository/`、
`ystv-data.zip`、`ystv-data-manifest.json`。把 `repository/` 内容同步回工作仓库，
运行 `python tools/dataset.py verify`，检查差异，再提交或发 Pull Request。
工具只校验数据结构；姓名归属、证据可信度和分级仍须维护者核对。

维护者合并完成后记录源提交，把 manifest 中的 `source_commit` 写成完整提交 SHA：

```powershell
$commit = git rev-parse HEAD
python tools/dataset.py stamp --manifest ../YSTV-data-v2026.10.07/ystv-data-manifest.json --source-commit $commit
gh release create v2026.10.07 ../YSTV-data-v2026.10.07/ystv-data.zip ../YSTV-data-v2026.10.07/ystv-data-manifest.json --target $commit --title 'YSTV 数据 2026-10-07'
```

发布前确认数据包来自即将打标签的同一份 `data/` 与 `dataset.json`。
必须发布为正式 Release，附件名称固定为 `ystv-data.zip` 与 `ystv-data-manifest.json`；
草稿、预发布、普通提交和 PR 都不会被网站自动导入。正式版本应使用新标签，避免覆盖已经使用的版本。

## 网站导入规则

网站每天香港时间 04:30 左右检查此固定仓库的最新正式 Release；管理员后台“赛事数据导入”
可立即从 GitHub 拉取，也可以上传 ZIP。导入检查正式标签、源提交、附件及逐文件 SHA256，
校验完成后重算赛事、选手、胜率、荣誉和生涯/年度/累计 Rating，再原子切换公开版本。
输入与计算规则相同则复用现有版本；失败继续使用旧版本。连接失败后每 10 分钟重试，
连续失败满 1 小时停止，等待下一次每日检查或手动导入；校验失败不会自动重试。
**TOP20 和所有资讯不会被导入或改写。**

## 许可与来源

整理数据采用 MIT，可复制、修改、再分发和商业使用，保留许可和版权声明。
游戏与第三方原件的权利归各自权利人，仓库不分发原始表格。
来源名、SHA256 和记录坐标用于核验；原件仍由资料维护者保存。
