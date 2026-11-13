# Stage0正式前一次静态实质审阅

审阅UTC日期2026-10-21；精确起止时分UNKNOWN。实际model / effort UNKNOWN。**accept=false；must_fix=2，正式核算尚不应启动。** 唯一Owner已收到对应最小修复，不需用户重复授权；只复核整改，不扩大经济设计。

绑定实现SHA `5fe25bb7a2773883648dede3964d297c217d4801b88bc4965ca59340a4d471b5`、seal `5946a8a52ae02380dc74e73fb5369b0460962b244119c21a15674dfcfc3d0b14`、review-package diff `19011912bcdc5e0e7e79b711eba033195666c3c183bebf79ea8c33aefc74e27f`。本轮本地hash核对与提供值相同；不读行情核输入hash，输入实际SHA/CRC复用preflight原件。

## must_fix

1. **冻结输入身份未在formal直接绑定。** stage0.py L284–298验证代码/测试/preflight身份，但L294重新safe_inputs（L80–99）从共享旧data-receipt取得expected hash/rows，L296只对该动态值核实际输入，未比较本次seal.inputs。共享回执与输入同时变化可能通过，尽管本次冻结输入已变化。最小修复为strict比较date/path/expected_rows/expected_sha256/actual_sha256与本seal中的固定身份，再核对应文件；不能把更新共享回执视为新授权。无需重做真实经济或再下载输入。

2. **正式预算初始化异常落在首失败保护外。** main L320的Budget在try之前；其L53–61异常不会进入L328–334写terminal-stop，也未生成formal-started，不能依既有标识阻止把正式入口失败当未开始再试。请将正式预算初始化纳入首次失败保护；保留既有STOP及已运行标识的只读拒绝语义，不能覆盖首STOP。对应异常合成检查即可，不需触真实报价。

## 已审逻辑与证据

- L115–149流式遍历gzip至EOF/CRC，同local_timestamp只yield批末；L228–240按≤u/v as-of、端点不后移，L198–217年龄/非法报价作为未知。网格常量L27与parameters一致，日首60秒/每2秒/尾2秒排除。取下一批用于流式推进不把其报价送入前一端点。
- L152–160核25档有限正数、价序及不倒挂；L177–195用精确Fraction逐档买4000名义、卖同数量，买滑点1.0001/卖0.9999与每边.004仅一次，美分向上；未知不分入正零负。L235–263保存全网格引用身份、重叠原因及固定统计；L305–310只按可核正空间决定STOP/待Root，不当预测信号、收益或容量证明。
- 实读test-stage0.py静态手算fixture及synthetic-tests.json，18项PASS；真实输入打开数0。首次固定网格单位错误在合成时失败，失败resource保留，不冒称正式失败。合成目前直接核groups/ref/score_pair及cash_flow，不冒称已运行真实screen_day。
- preflight.json三日身份、gzip CRC、日期/行数/同戳计数及实现/方案绑定已记录。其11820B原件SHA与seal一致；synthetic-tests.json实际名已确认，SHA `bc591226e36141699ceeda04e623885d29a252325aa56f2dafc3715e8149985b`与seal一致，不是不存在的synthetic-results.json。
- L51–77预算实际为stdlib单线程、峰RSS/磁盘/累计wall检查、CPU及SIGALRM；失败/成功合成与真实preflight资源原件均已读。前检wall累计7.593090874s，另10s明确保守预留不冒实测；ready-budget与manifest实际记录保留。未把峰内存预检值当未来正式保证，预算超限须停止。

阅读：复用root/stage0-owner-brief.md，完整静态stage0.py/test-stage0.py（diff及直接编号文本交叉），owner/report.md、preflight.json、parameters.json、preflight-seal.json、synthetic-tests.json、3份实测resource及preparation-reserve、ready-budget、owner-manifest与root diff。未重跑测试、formal、QC或任何金融计算，未读缓存CSV/合成gzip/行情数组/权重，不联网、不取数据、不触保护Library。只新增本review，不改Owner/Root原件或旧A/B STOP。
