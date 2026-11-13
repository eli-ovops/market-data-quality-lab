# 两日成交流历史挑战：终态报告

唯一正式进程已成功退出（exit 0），状态为 `HISTORICAL_MECHANISM_CANDIDATE_ONLY`。本报告只汇总封存结果，不新增计算；独立终验由 Root 协调。预检历史完整保存在 report-preformal.md。

## 固定结果及边界

|项目|2026-05-01|2026-06-01|
|---|---:|---:|
|原生成交报告|29634|45088|
|固定观察域分母|29616|45085|
|合格未来参考标签|29615|45040|
|每日 D（bp）|0.1475064198609573|0.13507305103921827|
|主费用固定1秒退出正余量报告|0|0|

合并 D=0.14128973545008777 bp；预定1999次日内分层区块抽样全部有效，type7 95%区间为 [0.08996441189022865, 0.19042348129101727] bp。因此仅通过冻结历史机制候选门槛。D比较按方向标准化的预警选择与固定hash选择之不利选择标签，不是策略账户收益。

辅助结果为 `NO_POSITIVE_QUALIFIED_SPACE_FIXED_1S_EXIT`：假设获得原被动成交价、固定1秒退出、买卖价执行及1bp不利滑点、入场0.3%/退出0.4%费用，两个固定日全部合格主费用余量不为正。此项不阻断主统计，也不能扩大为其他退出机制的否证。费用为冻结假设，个人实际费率仍 UNKNOWN。

本任务没有证明个人能实际获得这些成交、及时撤单、可交易容量或净利。未重建个人队列、未验证本机网络/撤单时延。接收钟/源钟量化guard仅是供应商字段条件。May/Jun属于已披露既有QC及跨任务暴露的历史挑战，不能称绝对盲测；固定新规则于本次正式标签前封存。

## 原件与一次性执行

- 冻结实现及参数：core.py、analysis.py、run.py、tests.py、parameters.json；preparation-seal.json 绑定实际3.12.14解释器与所有哈希。旧runtime元数据及必要修订保留在 before-runtime-binding/ 和 runtime-binding-amendment.json。
- 正式：2026-10-22T00:19:32.729767Z 启动，00:28:16.139355Z 生成结果。tool session=32302，PID=59667；只启动一次，exit=0。formal-launch-receipt.json、first-started.json、formal-completion-receipt.json 与原始 formal-stdout.log/formal-stderr.log 保留；stderr为空。
- 固定288次行情GET全部HTTP200、完整读入，实际传输2,838,806字节，无重试。原始响应在 data/，GET-ledger.jsonl、raw-QC-ledger.jsonl、data-seal.json 及两日data-seal绑定身份。数据封存先于正式标签计算。
- 两日summary和coverage原件、result.json保留固定分母、未知原因、每格订单/网格数、区块与极值见证。不因未知删除固定分母，不以费用结果选择样本或调参。
- first-stop不存在是此次正常完成的事实；first-started仍永久防止重启，不表示允许新单元。旧实验/Stage0 STOP未改。

## 资源与权限

正式阶段：计算12.865506364149041秒，网络222.40563617186854秒，串行间隔等待288.1809180059354秒，总墙钟523.4520617499948秒；进程CPU16.923449秒，1线程，峰RSS156827648字节，当时新磁盘11409573字节。

正式结束时累计预算扣账：计算207.70245232316665秒、网络282.40563617186854秒，已包含 Root/辅助保守预留计算190秒、网络60秒；这些预留不是测得用量。下载2,838,806字节另加Root预留1MiB。最终文件级封存小额计算另在 resource-file-seal.json / final-budget.json记录，未重置此前资源。全部仍低于1800秒计算/网络、64MiB下载、512MiB RSS、256MiB新磁盘及01:59:57Z主动截止。

新增付款、安装、注册、模型/训练/权重加载、账户/钱包/交易均为0。未访问保护Library路径。真实agent model/effort=UNKNOWN。规则版本 PERMISSIONS-2026-10-14-v1、ROUTING-2026-10-13-v4、HANDOFF-2026-10-10-v2。

终态文件级身份见 final-manifest.json、final-budget.json、terminal-seal-receipt.json；本 Owner 仅等待必要文档澄清，不继续下载、分析或后续实验。
