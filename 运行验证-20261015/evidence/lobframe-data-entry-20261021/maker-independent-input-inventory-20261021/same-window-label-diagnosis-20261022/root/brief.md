# 精确同窗既存标签诊断：唯一要求

用户已明确批准完整只读标签聚合。先读同目录authorization.json。Owner仍lobframe_label_timing，Reviewer仍lobframe_minimal_economic_review；不新建替身/子agent。你不独自在代码库，不回滚他人编辑，只写自己分区，旧任何实验/标签/源码/summary/seal/结果/STOP原件不改。

## 目标与固定样本

核2026-05-01、06-01两日，各原决策网格grid_second=5..32449（含两端，UTC00:00:05—09:00:49）。原coverage中grid=(capture-daystart-1)//1s，因此所对应观察区间为(grid,grid+1s]，不是简单capture<09:00:49；严格沿原定义，最后一格观察可至09:00:50。该窗口实际约9h，不能为“9h”字眼改成09:00:00或09:00:05。标签目标约成交后1s，直接使用已存label及状态，无查询报价/新未来标签。

仅读execution-20261022/owner两份coverage.jsonl.gz、summary、原manifest/terminal seal/参数及analysis.py文本；现金/费用原件仅解释。新helper不能import原analysis/core、跑信号/grid_states、label_reference、futureguard/choose_first、auxiliary、策略/风险/收益回放。原coverage selected_first及reference/time/tie/zero/no-score状态原样保留；不在截取后重选ID、不用后继替UNKNOWN。

保持原四cell顺序[z_buy,z_sell,hash_buy,hash_sell]，只将status=selected_first、合格既存label、hint==passive_side的行纳入该cell；保留非入样/未知原因与分母。先同网格订单等权(mean=math.fsum(losses)/n)，再每方向/政策有效网格等权，最后买卖方向各1/2；D_day=.5*((L_zbuy−L_hashbuy)+(L_zsell−L_hashsell))。D>0表示信号提示集合更集中指向之后不利成交，不是F赚到的钱/准确率。四个均值、每cell有效ID数/订单数/网格数、标签覆盖分母/分子/未知、状态/原因计数、两日D必须全部报告，未知不记0。原覆盖80%、每cell100ID等要求原样，若不足只能有限描述/UNKNOWN不能晋级。

## 方法与执行次序

执行Owner先只写helper、method-spec、人工合成、输入身份与diff/准备封存，不读取新同窗D后再选方法。Reviewer在同窗结果产生前先审method/窗口/权重/未知/不确定性适配，再审helper/合成原件；Root绑定seal内部放行后唯一正式聚合。原始coverage全文hash及gzipEOF/CRC可以在正式单次读取内确认，数值聚合一遍；不需重新读原行情、生成或核算未来标签。可同时做原全天已有统计的引用一致性检查作为实现验收，不能当新增独立效果；若要将其放在正式扫描中必须事前写清。

不确定性不按结果挑：沿旧30分钟联合四cell块、seed20261021、1999次/type7/至少1900有效的框架。候选适配为按原UTC块号0..18保留精确窗口截取贡献（首尾短块不丢、不延窗），每日至多19块抽19块；两日原equalweight只可作补充，主文两日分别D/描述性区间。该必要窗口适配须Reviewer在结果前评议固定，若不合适可在看结果前采用更简且可解释的固定描述，但不能因结果改。不确定性只能聚合既存标签/块摘要，不是重算标签或策略。需披露短窗口/短边块/相关性、历史已见及原统计选择限制。

合成覆盖：两端格、capture与grid相容、selected_first/后来同ID/未知不替补、无提示/零分、同网格先订单等权再网格等权与方向各半（不混成逐笔均值）、四cell有一空应DUNKNOWN、首尾短块都留、无新标签重算；合成不得读取行情结果。有意义的检查即可，不复制实现自证。

正式单次小聚合完成后，不根据正负修复再跑、不选方向/子窗口或阈值。正式前可修合成/代码必需问题于原帽内；触帽停，不自动加时。期限和资源auth：30分钟主动、总30CPU秒/1线程/128MiB/新2MiB，Owner20+Reviewer/Root10，新付费/网络/数据/安装账户钱包交易0。原保护Library完全不碰。实际model/effort/speed UNKNOWN，路由规则沿现版本。

## 交付与归因

Owner输出两日精确摘要、固定不确定性结果（若预审允许）、输入hash/真实CPU/wall/RSS/PID/exit、helper源码/spec/合成/封存、白话报告。Reviewer审全部原件/已存scalar，不重跑Owner聚合、不重扫coverage；Root实读报告及身份，不重跑。

如两日同窗条件信息仍正且描述性不确定性支持，失败位置更可能在信号→报价/成交/库存→净收益转换；这仍只是定位、非因果证明或赚钱。若消失/反转/覆盖不够，则信号在本精确窗口的可运输性/证据本身也有问题，不能只怪费用。若混合或区间跨0，需如实未能明确区分。旧全天D不能冒本窗口，本窗口D不能直接减手续费或乘本金，不与8格收益凑独立样本。无论结果均不推翻原固定组合现金必要条件失败，不自动恢复模型/策略/交易或扩新方向。

## 接口检查

|任务|输出→消费|约束|
|Owner聚合→Reviewer|原selected_first/标签→原权重D|不可新造标签、补选ID或新均值|
|窗口→观测及块|5..32449网格→原capture映射和UTC块|最后格完整、边块保留，不挑窗|
|Owner准备→正式|合成/spec/seal→Root release|无正式结果前先方法与代码审，唯一聚合|
|同窗D→现金解释|条件信息定位→旧F/H毛/净差|分母不同，不认证自身获单/alpha/容量|

本次是现有证据的指定聚合，不是新交易项目。临时/证据文件在本单元记录用途并保留，不删除旧数据。
