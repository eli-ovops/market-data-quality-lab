# 两日挑战：准备完成，等待内部正式放行

2026-10-22 UTC00:14后准备回执。唯一执行Owner lobframe_label_timing；规则沿PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。目标沿原路由，实际model/effort UNKNOWN；不以配置冒充运行模型回执。本单元无拟合或权重加载。

## 当前状态

完整已批方案SHA256 `39b9b801e57404b2c5cd48b5e7bb6ea4d53e1ae301f724c487904db3bb90b5ea`、authorization.json及相关规则已读。准备代码/参数/合成检查和两份既有BBO缓存身份预检已完成；**新增行情GET0、正式标签0、账户/模型/交易0**。旧实验及Stage0 STOP均不解除。等待Root协调既有两Reviewer闭合并写当前整单内formal-release，不请求用户再次许可。

## 版本与入口

- `core.py`：单线程资源/下载账、唯一固定288片URL、拒绝重定向/重试、gzip或HTTP identity、分片QC/断连/原始trade封存；SHA `a35e566ba8f4beef90669432717af50f3f74b8f1d7e9f8594305558f96cb8097`。
- `analysis.py`：整数时间与量化边界、BBO参考、唯一首次被动ID、原分笔计数z/固定hash、方向标准化D、固定分层bootstrap和辅助费用；SHA `bda1df10cf210f4f794555387cac37206638d2c775b898568cbb56d6d21c012d`。
- `run.py`：preflight或唯一formal入口，first-started/first-stop、冻结输入身份绑定及连续一次取数—QC—封存—条件分析；SHA `430b521c3e1e6a9dde249cc2805ee61682701b37a54a2be5c6df61ff16091b91`。
- `tests.py`：无网络、无真实标签的合成检查；SHA `550713074b98fb98d943f9198c39d5e393e9e9278d13de6dc5e632dc5a14b7a6`。
- `parameters.json`：具体量化/去重/计权/缺口/成本/RNG/预算默认值，SHA `d2b305616c9964c7de848c4524ec6aef3291779e071cfbae3fce59a6dc45539f`。
- `preparation-seal.json`：SHA `f2a724017607c944f32da7cbf0ddbef0503d65fa9ae5300704fd6550cbe34a99`；绑定上述源、原件、参数、Python版本、实际缓存身份与合成结果。

正式协议：Root独占`../root/formal-release.json`，status=`RELEASED_ONE_TWO_DAY_UNIT`、preparation_seal_sha256必须绑定当前seal。只有内部放行后才可一次运行`run.py formal`；同一进程连续阶段，失败或首STOP后禁止重启。当前没有启动它。

## 时间与首次选择裁定

Root在新行情/正式标签前澄清并确认，已落实：原生7位接收钟±1个100ns tick；原生microtimestamp和CSV capture/source均为整数µs域±10ticks的量化假设。参考capture上界严格小于目标下界、最坏年龄≤1秒；BBO源钟下界严格晚于trade源钟上界。未来trade源钟与截至t严格capture<t的全部已知trade最大源µs作严格大于比较，同值/回退UNKNOWN，不从未来补max。

全日固定观察域内先按时间/source guard与未来参考合格确定首次被动ID，再接z/hash。首次无评分/零分不可换后续；首次同capture并列整ID UNKNOWN，不借行序定序。输入断连/边界未知也不允许用后续成交救首次ID。全部时钟仍只支持collector/字段条件，不认证用户撮合前行动。

其余前置固定取舍：最晚名义as-of报价与目标量化区间重叠时记UNKNOWN，不跳回更老报价；下一名义报价的区间与目标重叠亦UNKNOWN。BBO同capture组按数值四个BBO价量字段判冲突；不重排源钟。有效区间首次ID共同于两政策，hash仅在同一非零z网格提示。分日30分钟48块、四个政策/方向cell共同重采样；stdlib Random(20261021)，1999次，type7区间，版本已封存。

## 验证原件

1. **43项当前合成检查PASS。** 精确时间、接收/源钟边界、1秒最坏年龄、同源/回退max guard、同capture首次歧义、零/无评分不替换首次、分笔而非unique-ID、断连闭区间跨片、空gzip静默、identity响应、重复tradeID/异常type/片界/坏CRC拒绝、手算标签符号及双侧费用、订单/网格双层权重、方向标准化手算D、分层bootstrap与缺方向复样均覆盖。合成QC只写各自fixture目录，不污染真实下载/QC账。
2. 初始34项及后续增加统计手算的43项结果均保留，各有resource记录。没有合成失败或正式重跑；增加检查针对D计权/区块算法，未读真实结果择优。
3. `preflight.json`：May/Jun两缓存压缩SHA与旧data-receipt一致，完整gzip EOF/CRC、snapshot25字段集合/身份、UTC日界/时戳单调和行数通过。没有查看/计算正式标签或行情效果，未复制CSV。
4. 真实预检之后只将已有cell聚合块提取成纯函数以做手算测试；核心输入解析、入口、参数未改，因此不重复真实QC。`preflight-reuse-amendment.json`明确关联；`preflight-source-snapshot/`保存按先前hash校验字节一致的旧分析/测试版本，非重新运行。

## 资源

`preparation-budget.json`累计扣减：计算194.789711秒，其中Root终验180秒和辅助文件准备10秒是明确保守预留而非实测；Owner合成与缓存预检实测约4.789711秒。网络预留60秒、文档下载预留1MiB均先扣账；Owner行情请求与下载为0。实际记录峰RSS55,738,368字节，单线程，远低512MiB。全部源/参数/报告/测试/资源/小fixture列manifest，当前无大缓存复制或未记录临时文件。

正式下载可用预算须在上述已扣量之后检查，不另给每Owner一套上限。第一笔10分钟单通道请求尚未实测；其失败按输入失败保留并停，绝不改分钟/日期救场。整单主动截止仍为UTC2026-10-22 01:59:57，不因等待或阶段重置。新增付费/安装/注册0；无凭证、账户、钱包、模型、自动化；保护Library没有read/stat/hash/search。

未完成：两Reviewer静态审阅与Root内部放行、唯一正式288片取数/QC、条件统计/辅助费用、原件验收。当前仅preparation ready，不声称输入已齐、统计通过或可赚钱。

## Formal runtime binding correction

The original seal writer used Python3.9.6; that field did not describe the tested/formal runtime. The exact execution interpreter for both synthetic tests, preflight and intended formal run is `/Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/.venv/bin/python`, actual `3.12.14 (main, Aug 25 2026, 13:50:33) [Clang 22.1.3 ]`. Prior seal and runner are retained underbefore-runtime-binding/. New formal startup validates both sys.executable and sys.version against seal.formal_runtime before input hashes/GETs/labels.

Four metadata-only guard checksPASS, including reject writer3.9 and wrong executable, and match original preflight3.12.14. No true QC or labels rerun; original43 checks/core/analysis remain unchanged. runtime-binding-amendment.json binds old/new identities. Current seal SHAf2a724017607c944f32da7cbf0ddbef0503d65fa9ae5300704fd6550cbe34a99.
