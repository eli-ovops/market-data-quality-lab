# Stage0准备回执：ready_for_formal

UTC 2026-10-21T11:36:30.905629+00:00。唯一执行Owner lobframe_label_timing；实际model/effort UNKNOWN。当前只完成必要适配、合成测试与三缓存身份预检，**未正式成本核算、未取Kraken、未拟合/预测、未创建未来安排**。Root/既有Reviewer闭合并在当前授权内放行后，才允许唯一正式Stage0。

## 版本与验证

- 方案SHA：d1621c849ce25d66c81e8121c46186e78eaabb759d3a75ca347ae6937c595d50
- 独立stdlib实现stage0.py：5fe25bb7a2773883648dede3964d297c217d4801b88bc4965ca59340a4d471b5
- 合成测试test-stage0.py：77aa199a350ad647d751aef7fcb3001df54fc73980f2c97b4468777c8a55200e
- preflight-seal.json：5946a8a52ae02380dc74e73fb5369b0460962b244119c21a15674dfcfc3d0b14
- 18项合成检查通过：手算正/负/零净额、双边美分向上费用、双边滑点仅一次、多档数量步进与不足、同戳批末、端点含等号与过龄、未来状态拒绝、缺失不填负、日界、网格边界、type7分位数。
- 首次合成失败保留：fixed_grid_boundaries拦住END_US单位常量少1000，未打开真实输入；修复后完整重测通过。失败资源回执和首批fixture未删。不是正式失败/重跑。
- 真实预检只流式核压缩SHA、完整gzip EOF/CRC、字段集合/宽度、交易所/币种、双时戳UTC日界与单调顺序、总行数及同戳批计数；**未计算报价经济结果，未声称所有25档价格/深度已经济可核**，必要引用状态25档校验留给正式阶段。

| 日期 | 行数 | 实际SHA与旧回执一致 |
|---|---:|---|
| 2026-07-01 | 258996 | b237f83aaf11924c179ddc6b1c2c356d16a662220316a17ce3cf523a4a56ddae |
| 2026-08-01 | 252246 | 26958886305d7235f73d2f53e146691b055e9612d81098e46a427af55acbd9bb |
| 2026-09-01 | 260356 | 6efebc58901215c38f37ecdd6b745aeebf57f62463ae7d34f75420a3ee4cb40f |

## 算法/安全默认值

只读三份项目原缓存；逐组件拒绝symlink，resolve必须留在原项目data目录，不复制CSV。流式迭代同local_timestamp仅保留批末状态；每腿≤端点as-of、年龄≤1000ms、固定名义u/v。精确Fraction用于25档买卖、费用取整及正负号，48位Decimal仅展示；未知原因/重叠计数独立。日内43169网格全部端点引用行号/批起止行号/时间戳/年龄写小型gzip审计账，未另存盘口。固定最值/分位数与少量预定见证，无费率或子样本搜索。

标准库单线程，无数值库/模型加载；频繁RSS/磁盘/wall检查、CPU硬帽和SIGALRM按累计计算及主动截止先到即停。一次正式标识、首STOP保留与实现/测试/输入哈希检查；任何正式异常不重启，不能借重进preflight清除。Root放行文件约定见parameters.json，必须绑定本seal。

## 资源与下一步

合成失败+成功及真实预检实测墙钟合计约7.5931秒；另外保守预留10秒覆盖短辅助命令和计时前启动，不冒充实测。累计预算扣减17.5931秒；CPU实际值分阶段保留于resource-*.json。预检峰RSS28,327,936B；新目录当前约数十KiB，ready-budget和manifest列实际大小。全部0新增下载/安装/付款，无账号/交易。总帽3600秒、2GiB、512MiB不变；主动截止UTC15:26:52。

待验收：既有Reviewer静态审实现、测试、参数、预检及seal；Root正式放行。未来正式结果尚UNKNOWN，不声称存在或没有空间。本回执不是完成整个Stage0。

文件均保留；owner-manifest.json列本Owner全部新文件的路径/大小/hash（manifest自身不自引），包括失败fixture与资源记录。Root/review他人目录不改；保护Library从未访问。

## 正式前保护修订（2026-10-21T11:51:58.974022+00:00）

两项must_fix已作最小修复，待原Reviewer闭合；正式仍未启动。formal逐项将当前date/path/rows/hash与本次seal.inputs比较，封存actual_sha256必须等于expected_sha256，实际文件仅对该封存hash核验。Budget初始化进入try/首terminal-stop保护，旧STOP只读拒绝且不覆盖。

新增人工身份漂移和隔离OUT的初始化失败/首次STOP保留/拒绝重启共11项PASS；真实缓存重读0、经济计算0。真实解析、报价计算、时间选择、预检及Budget类本身源码均未改，原18项fixture与真实QC按protection-amendment.json的定义源码hash复用。合成terminal-stop仅写owner专用fixture目录，真实stage0无formal-started或terminal-stop。

旧实现/测试/seal/报告/清单保留在before-protection-amendment/，未复制resource-*.json。新代码SHA 05795585da12a56af7cc6c7d47a31a9053e4963674ea968292f7a0a84247bcaf；新seal SHA 91275c145ade058d238c2c7ab9d318ec2e2341e0fe297559202e1efd29d3e8ee；diff为protection-amendment.diff。累计计算扣减17.616838832秒（含10秒保守预留，未清零）；未运行进程，仍在原帽内。

## Final Stage0: STOP_NO_POSITIVE_VALID_SPACE

PID70270 / tool session69329, one launch, exit0. Started UTC11:54:39.818559; completed11:54:55.265327. This is the predeclared economic STOP, not an exception/resource failure. Raw formal-stdout.log and empty formal-stderr.log retained.

| UTC day | grid | valid | unknown | positive | negative | maximum net USD per fixed4000 nominal |
|---|---:|---:|---:|---:|---:|---|
| 2026-07-01 | 43169 | 42804 | 365 | 0 | 42804 | -28.7463392939746794145537858794126221714787312420 |
| 2026-08-01 | 43169 | 42774 | 395 | 0 | 42774 | -31.1372813992761433039820794693843418750360246888 |
| 2026-09-01 | 43169 | 43031 | 138 | 0 | 43031 | -30.1207222564163937072924302859982178785143318123 |

Totals:129507 grids,128609 valid(all negative),898 unknown,0 positive,0 zero. Fixed main assumptions only:4000USD nominal,0.40% fee per side rounded up to cents,1bp adverse slip per side,25-level visible depth,as-of reference endpoints. This is necessary ideal quote space, NOT causal predictions, account PnL, executable profit or capacity proof. Unknown ages/depth are separate, with overlapping and joint reason counts; never negative/zero imputation. Cannot conclude all times/strategies lose.

Daily stage0/*-summary.json contains fixed type7 quantiles and fixed/minimum/maximum witnesses. Full grid endpoint identity(data row,batch first/last row,local timestamp,age) and cash details are retained in *-endpoint-records.jsonl.gz; no orderbook copy. Input rows258996/252246/260356 match sealed identities, compressed hashes checked against seal before formal use, and all gzip streams consumed through EOF/CRC. No postrun market reopen or economic recompute.

Formal wall15.563475583s,CPU15.436076s,peakRSS32571392B,one thread. Prior+formal Owner computation33.180314415s including10s explicitly conservative preparation reserve; file-only sealing below adds its own receipt. New unit disk at formal end12230998B. Root/reviewer resource aggregation is separate and not measured by Owner. Downloads,installs,payments,accounts,orders,models all0; actual model/effort UNKNOWN.

terminal-stop.json is permanent. No Kraken,no M0/M1 fits,no waiting for Nov or future arrangements. Jul-Sep now additionally have this ideal-cost observation; preserve earlier prior-use report as its as-of record, not a claim about this later observation. May/Jun not read here. Pending Root/reviewer evidence acceptance only. Frozen code/tests/seal unchanged.

File-only sealing initially hit a stdin Non-UTF-8 SyntaxError before execution; LOCAL_BLOCKERS lines809/855 supplied supported ASCII-script fallback. Formal itself was not rerun or changed. Failure overhead is covered by existing10s ancillary reserve. No files deleted.
