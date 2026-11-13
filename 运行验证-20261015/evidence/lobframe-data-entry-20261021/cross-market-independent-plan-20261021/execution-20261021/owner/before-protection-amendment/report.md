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
