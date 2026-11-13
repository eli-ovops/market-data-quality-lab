# 正式终态：来源、输入与资源窄审

结论：PASS_WITH_LIMITS（来源/输入执行绑定）；本范围无新增 must_fix。经济终态保留 `UNKNOWN_NOT_ECONOMICALLY_IDENTIFIED`，不能晋级为已识别净利或真实获单。实际 model/effort：UNKNOWN。

本轮仅静态读取 Owner 源码局部、封存/起止/资源/两日 summary/result/manifest 小原件，并校验其中14个小文件的长度与 SHA 及 terminal→manifest 绑定；全部一致。未重读任何行情、压缩原行情、逐笔账数组，未运行 reader/合成/模型/回放，未联网。完整经济状态机由另一 Reviewer 验收。

## 实际执行与版本

`owner/formal-started.json`：2026-10-22T10:35:36.439637Z，PID32610；`formal-completion.json`：10:36:34.944252Z，exit_code0。`formal-exit-receipt.json` 将该 PID、session12439、工具 exit0、attempts1、stderr0字节及 no_retry 绑定；起止与终态一致。首次 marker 采用 `run.py:17` 的排他创建，正式入口 `run.py:170–176` 在实际检查前写 marker；本审未重新启动。

正式 release 与 preparation seal 均固定 `7190a66de5030fa63514f6bac0266b959692d49fcce926daef2cfd9eecc19b07`。当前小源码的 hash、formal-started.source_hashes、manifest 一致：

- inputs.py：`e460a6b91884e79c14c1ba9d17c695e2df69e081d8de8d533e0b0a64c10313e0`
- run.py：`0e6c1dc7add58e3993949a45bfc7f00f191c3424606cfee174325dcbcb3ac2ee`
- core.py：`47117ada2e0e301b1ac48b31ab8ffa0ec80194b68a416c21edb0852f0b899076`

实际解释器 `/Volumes/EXTERNAL/亚力克斯 /运行验证-20261015/.venv/bin/python`，3.12.14；正式代码 `run.py:80–89` 要求 release/seal、runtime、源文件、authorization、输入 metadata/stat 同一，和先前通过的 reader 审查绑定相符。

## 两日实际输入与终端摘要

|UTC日期|trade固定前缀|book capture组|同capture冲突无效组|终端评价capture（100ns ticks）|原book行|
|---|---:|---:|---:|---:|---:|
|2026-05-01|5761|87482|1|17776260517286490|87483|
|2026-06-01|9318|90870|1|17803044510000000|90869|

固定共同前缀含暖机，至09:00:52；两日 summary 与既有 input-readonly-precheck 计数/终端行一致。May在09:00:51严格参考不合格后，采用首合格 arriving 09:00:51.7286490（源钟09:00:51.700864）；Jun在09:00:51评价，引用先前capture09:00:50.9196430（源钟09:00:50.891157）。后两组参考钟来自既有输入QC，不是本轮再次遍历实测。`inputs.py:42–52` 的严格asof与首合格终端规则未改；终端行不是基于未来价格挑选。

seal.inputs.raw 明列110个小片，每日55个。`inputs.py:83–86` 对每一待读片先完整压缩 SHA 比较；`run.py:91–95` 两日都须完成 load_trades 和固定5761/9318计数后才能输出对应 summary。两日 summary 与正常正式完成共同构成这些 guard 实际经过且未报漂移的执行路径证据。**没有独立逐片“hash检查通过”末端清单，也没有本审重新hash110个行情片**；不把上述执行路径证据写成 Reviewer 独立重算。

BBO仍是旧May/Jun缓存：封存旧 SHA 分别 `e599b118af934cfe45dc3df81330a364b60bf61008d456be674c452a2d3cb246`、`a50227978d36712ef34413aedea58bb64e6f8df4f6a6106b23ff1b5bef6c5830`；正式固定stat/metadata，summary明确 large_file_hash_not_rerun、old_full_CRC_not_rerun 均true。不得宣称本轮重新完成全日SHA/CRC或全部feed完整性。

## UNKNOWN的输入含义

- `core.py:67–82`：有库存时，当前严格参考不可用记 `reference_unavailable`；可用参考深度不足则记 `depth_insufficient`。summary 的 risk_unknown_count 各路径非零，展示的首批原因是 reference_unavailable。它是风险计量参考未识别，不能用终端有quote倒推中途全路径都有合格参考。
- `core.py:129–136`（本轮先前已读静态源码定位）：实现先做post-only检查，再要求ownL位于当时同侧25档价格的[min,max]内；不在此区间即记 `accepted_price_outside25` / `UNKNOWN_queue_outside25`，当前冻结实现未对该价位赋队前量。这一记录可能同时涵盖真实同侧更深界外的数据缺口，以及价差内改善报价被当前模型域排除的情况，不能全部解释为必须新增更深数据。它不是交易所真正已接受的订单或实际账户ack。本轮未逐事件重读book，不知道两类所占比例；此文字限定未改正式代码、数据、结果或PASS_WITH_LIMITS结论，亦非新实测。
- 两日各8条条件路径全为UNKNOWN；8个F/H比较亦UNKNOWN。result的总状态与这些引用缺口一致。此为有意保留的数据/模型识别边界，不是工具异常，不支持修连接、自动重跑或用部分数值宣布获利。格式100ns、源钟微秒及其格粒度均不能认证时钟准确度、用户本机延迟或个人行动性；真实队列、个人获单仍未证明。

## 资源与封存范围

`resource-formal-1792665394945097000.json`：正式wall58.52215175秒、CPU55.352344秒，先前Owner准备CPU0.196066秒，累计55.548410秒；另60秒是审阅保守预留，不是实测CPU，账面含预留115.548410秒。RSS峰值83,525,632B，1线程，network0。terminal seal另记文件封存CPU0.026885秒、wall0.06351575秒，应另计，不能漏写成所有收尾零开销；仍显著低于共同600秒预算。

正式资源回执写入前Owner输出25,741,653B；terminal seal写入前25,757,630B，两者时点不同，不是矛盾；都不是整个项目或整单元所有Owner最终占用实测。未为计量重扫行情或整个项目。

`final-manifest.json` SHA `9998ffe8a57a0bcd89b652ed7e0d98b84e96b2a22a272d3ea802f4fb6ec9c806` 已与 terminal-seal.hashes 核合。两日summary、result、源码、start/exit/resource、report等14个小文件与manifest实际hash/长度核合。两份压缩输出账的字节数/hash及行数仅复核其manifest/summary记录，未打开或重新hash大账：May1,213,205行，Jun1,108,782行。result SHA `fde97a75a504c1f20b167574759156b15df372ab53143ff5e96e9a3e7214ad67`。manifest按说明排除自身和terminal seal；非对所有输出逐项独立重新验算。

通过仅指封存输入/实际执行/输出引用的一致性和UNKNOWN诚实保留。供应商采集记录覆盖不等于上游feed完整、snapshot原子性、真实逐单队列或个人可及性；本轮不新增任何这些证明，也不对正常UNKNOWN开启重试。

审阅保存UTC：2026-10-22T10:41:16.712721+00:00
