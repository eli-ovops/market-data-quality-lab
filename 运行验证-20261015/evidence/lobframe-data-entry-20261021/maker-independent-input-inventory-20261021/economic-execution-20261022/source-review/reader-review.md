# 实际输入reader独立静态审阅

初审结论：**MUST_FIX_FIXEDPOINT_EXACTNESS（已由下文整改关闭）。** 这是实际源码审阅，不以旧缓存QC或26项合成PASS代替新reader正确性。已直接发Owner与Root；不代替经济状态机Reviewer。

审阅版本：preparation-seal SHA256 `5e29d47a073f8aaaa1ec90aeb0d1be96606da375ca6c92d40837dd1c8903d1a3`；inputs.py `5dcd15f2897578fb2ad50347d10e1730fe982ed22fe2c4845f407d602a3a9a84`。以下行号对应此版本，后续修订必须补审新版本。

## Must fix

inputs.py:19–25先以Decimal全局context做`d*SCALE`，再判断结果是否整数；core.py:6设精度60。乘法可能已把超过60有效位的微小非零尾数舍去，例如1后有很长的小数零及非零末位，原输入不在1e-12格，乘法舍入后却可能是整数，从而未兑现“12位定点不默截原值”。这不是要求接受更细输入：应在丢失任何原位数前精确判定可表示性，否则拒绝。可按Decimal tuple、足够局部精度或原值精确等价关系实现；不可只在舍入后的数上判断。

请仅合成覆盖：12位精确接受、13位非零拒绝、超过60有效位的非零微尾拒绝。现tests.py:27只测0.00000001接受，没有拒绝边界。此问题是代码保护与冻结口径矛盾，不宣称已发现真实缓存被截断；本Reviewer未读取真实价格/量或运行算例。

## 已核正确的输入职责

- **时间与量**：inputs.py:13–17从七位UTC分离整秒及尾数，整数100ns，不经浮点datetime转换；load_quotes:58的CSV capture µs×10一次，src保留µs，ref:34再乘10比较；raw cap/source:79–85分别保留整数。core.Trade:13–14量/价为Decimal。raw解析:82 parse_float=Decimal，91–93优先price_str/amount_str且与数值编码一致，有限正量/价；没有从normalized补造amount。单位假设在spec:19明示未独立认证，与输入证据一致。
- **身份/固定前缀**：load_trades:74–95每个小raw压缩SHA比封存账，原tradeID去重、0/1、双关联ID与源字段检查；固定至09:00:52，不改变日期。run.py:51–64从已绑定原metadata取得110个既存片及两日BBO路径；91–94固定两日5761/9318交易前缀数量。双订单ID仅验证，Trade对象不把它们当自己的订单ID；后续量消耗来源是raw而非历史对手ID。
- **完整100字段与冲突**：inputs.py:53–65固定104列schema，100价量字段都参与数值组比较；同capture任一冲突使bad累计保持，后续相同捕获时刻不能覆盖成好组。源低于此前最大src同样置bad，直到恢复；价序/交叉异常直接失败。bad将冲突与回退合并计数，日志名不应被解释为只有冲突。
- **strict-asof**：Quotes.ref:32–35先选择capture严格在前的最新组，再判bad/source严格在前/年龄≤1秒；最新失效直接None，不退到更旧行。equal参数有明确分支，不默认前视。它实现名义代表点规则，不认证真实微秒先后。
- **终端**：Quotes.terminal:36–44先ref(51)；无合格则从capture≥51开始按时间顺序找首个有效组直到52含端点，source严格早于其到达点；不检查未来价格好坏。该终端观察允许刚到达时使用。存在参考只证明字段/时间可用，不证明库存扫档足够。
- **原信号边界**：score_at:98–105保留100ns窗口边界不确定处理，数的是报告笔数，未偷偷按订单ID或数量改变特征。

## 绑定与合成覆盖限制

本轮仅对小代码/JSON/元数据重算SHA：五个source_hashes均与初始seal匹配；synthetic-receipt哈希匹配seal；四份既有metadata匹配；seal中的110个(date,offset,path,SHA)逐项等于独立QC summary原小片清单，prior_QC_summary哈希亦一致。没有重hash大BBO或读取行情。BBO新reader:47–48用size/mtime防漂移，原SHA/fullCRC沿既有封存，不是此次重新做密码学全体认证；该限制须如实保留。

synthetic-receipt记录26项PASS、无真实经济输入，已核对应来源身份。tests.py:29–39直接构造Quotes，确实覆盖strict最新无效不回退、陈旧及首到达终端选择；但**未走load_quotes实际CSV解析/同capture深层冲突入口，也未走load_trades raw quantity解析入口**。建议在正式前用极小合成CSV/raw文件覆盖字段/µs换算、深层同cap冲突/source回退、数量双编码不一致及12位拒绝规则。这里只要求与实际reader职责直接对应的合成，不重跑真实QC、不扩完整经济测试。

审阅读取：inputs.py全文、tests.py全文、spec.json、synthetic-receipt.json、preparation-seal的结构/相关metadata；core数据结构/数值context局部；run.py input_metadata/正式封存检查及调用reader段。没有运行Owner程序、导入模块、回放、模型、网络/下载/账号/交易；无保护Library访问。实际model/effort UNKNOWN。预算沿共同600秒，本Reviewer仅静态读与小文档哈希。

保存UTC：2026-10-22T10:26:11.400240+00:00

## 整改复核：最终PASS_WITH_LIMITS，无未闭合must_fix

新preparation-seal SHA256：`b486c559edd20e48ffb57c2167517a5bb49abfa67dca04c2127df8c29f32b18d`；新inputs.py：`e460a6b91884e79c14c1ba9d17c695e2df69e081d8de8d533e0b0a64c10313e0`。本轮仅读实际diff/源码/合成定义及小metadata，再对小源码/JSON核hash，没有执行修订代码。

- 新inputs.py:19–36从Decimal.as_tuple的系数与指数精确构造/整数整除，非零余数直接拒绝，不能由context60先舍尾通过；保留有限/非负与int64溢出保护。原must_fix关闭。
- 新inputs.py:101–104在raw价/量双编码核对之后，也调用精确12位可表示性guard；不会通过按float截断把raw数量导入经济模型。数量仍是显式BTC模型假设，非单位认证。
- 新tests.py:28–34补了精确12位接受、13位非零拒绝、超过60位微尾拒绝；35–52生成四行小gzip CSV，实际调用load_quotes，修改bids[20].amount造成同capture深层冲突，断言bad=[0,1,0]及最新无效不回退。它与前述直接构造Quotes的用例互补，未读真实行情。
- 30项synthetic-receipt全PASS，记录source_hashes与当前五份源码/spec及新seal全部匹配；synthetic回执hash匹配seal。新旧seal.inputs结构逐字段相同，只有输入保护和纯合成检查改变，没有借结果换输入/窗口。history/pre-source-fix保留旧原件。

新行号定位：capture整数在inputs.py:13–17；ref在42–45；terminal在46–54；25档schema/冲突及source回退在56–79；raw身份/Decimal在81–107。这些逻辑与初审正确项一致，输入精度保护改为精确判定，未发现新的must_fix。

本窄模块接受的是读取与参考选择实现/封存证据，不承诺真实队列、历史采集完整、个人实际可获单、真实物理单位或经济利润。BBO仅stat漂移核与旧SHA/CRC复用、同样本内和代表点模型限制不变；raw parser负向失败路径未全部各有独立fixture，但关键代码已静态审，30项合成不称全覆盖。这不替代另一Reviewer的完整经济状态机审阅及Root正式release。

整改验收保存UTC：2026-10-22T10:27:23.250728+00:00；实际model/effort UNKNOWN。

## 最终准备版本绑定（不重开reader审查）

PASS_WITH_LIMITS沿用至preparation-seal `7190a66de5030fa63514f6bac0266b959692d49fcce926daef2cfd9eecc19b07`。仅读preformal-amendment、新seal、history/pre-risk-fix旧seal与33项合成回执，并核小文件hash：inputs.py仍`e460a6b91884e79c14c1ba9d17c695e2df69e081d8de8d533e0b0a64c10313e0`；reader、run以及完整seal.inputs与此前已审b486版本相同。33项均PASS，回执hash绑定新seal；原100ns/12位拒绝/真实CSV深层冲突/strict不回退/终端首合格等合成覆盖仍在。

本绑定只接受reader模块与输入复用身份持续有效；core终端风险/CQ恒等guard及对应spec变化由经济Reviewer审，不在此重复验收。0程序执行、行情读取、金融计算或新网络，原must_fix保持闭合。

追加UTC：2026-10-22T10:34:10.448705+00:00
