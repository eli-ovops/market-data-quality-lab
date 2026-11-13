# 正式前独立静态审阅

审阅UTC：2026-10-22 10:26:23。实际model/effort/speed：UNKNOWN。仅独立静态阅读，不重跑合成、行情解析、回放或费用计算，不读取行情body/权重，不联网；无正式放行。

当前结论：NOT_READY，must_fix=[R1,R2]，已集中通知唯一执行Owner及Root。绑定当前preparation-seal SHA256 `b486c559edd20e48ffb57c2167517a5bb49abfa67dca04c2127df8c29f32b18d`。正式尚未开始。

## 必须闭合

1. **R1 终端多档退出风险估值重复引用原深度。** core.py L191–199先生成一次完整清算legs，逐腿调用fill；但fill L142/L158的observe仍以原完整book给剩余库存估值。已由本次退出消耗的首档在下一腿前重新出现在假想估值中，可制造不存在的权益峰值和回撤，影响F/H风险比较。最小修正为终端清算风险按一次原子退出观察前/后，或逐腿使用已扣除成交深度的参考；实际现金、费用及逐腿成交日志仍全部保留。需以多档终端合成原件闭合，不能只测终端现金。
2. **R2 规格声明的会计闭合保护未执行。** spec.json声明accounting residual must exactly0；core.py L204只写identity_residual，没有非零拒绝/UNKNOWN/首失败保护，run.py L101–109亦不核残差。已知参考且能分解时，非零残差不得成为完整路径或候选；参考缺失的既定归因UNKNOWN应保持其独立含义，不把归因缺失自动造作亏损。最小改动只落实已有会计保护，不加新盈利门槛。

## 已审范围与通过部分

全文静态读core.py、inputs.py、run.py、tests.py、spec.json、synthetic-receipt.json；审preparation-seal的源/运行时/授权/输入身份结构及尾部QC绑定，未逐条复核110份raw实体，未读取它们。阅读authorization.json及717faa原方案、e1e14 v2全文。Owner在阅读期间完成精度修复，最终读到30项合成回执版；旧26项不能代替当前版本证据。

- inputs.py L19–36以Decimal tuple整数余数检查12位精度，非零尾数拒绝；L101–104的raw价格/数量也同样检查，未静默截断。q明确向下取12位。L42–45严格as-of及年龄限制，最新冲突不向前挑好参考；L74同capture深层字段冲突传播到整组无效。
- core.py L87–139预留现金含买费、无裸卖、在途取消不提前释放；L159–186按固定方向/价格批次、source guard后消耗单份打印量，X仅严格穿价且按己方限价。边界计数不是实测时钟准确度。
- run.py L124–150接受前source最大值只用capture严格此前；同capture先打印、后任务、再决策；同capture不同价排序是spec固定模型选择，非真实撮合顺序声明。模型100/500ms不被称为个人实际时延。
- 买/卖现金库存及每腿maker费、终端taker费与滑点分开；终端深度实际legs不重复耗量。BTC秒积分、bid25深度毛名义、净变现回撤口径已在spec事前固定，F/H共用；R1仍影响该实现的风险数值。
- run.py L79–89绑定release/seal/runtime/源代码/授权及输入元数据；raw实际SHA在load时检查。BBO本轮用stat身份与先前QC/完整hash记录复用，不冒称本轮重新独立CRC。L166–183正式单次标记先于执行，首失败不重跑。资源含进程导入CPU、旧prepare资源累计，Owner540秒及review60秒共用600秒；保护仍需正式原件验收，静态检查不认证运行时实际峰值。

30项合成PASS仅是原件中报告的合成结果，不是本人独立执行，也不证明真实获单、净利、容量或外生成本为0。正结果仅可按四情景两日固定门槛作同样本内模型条件候选，旧结果和STOP不变。

## 同轮R1/R2整改闭合（UTC 2026-10-22 10:33:52）

最终结论：**READY_WITH_LIMITS；must_fix=[]**。只闭合原两项及直接影响，没有重开全实现审查或运行。Root仍负责按当前seal生成正式release；本审阅不是另一份执行许可。

- 当前seal SHA256 `7190a66de5030fa63514f6bac0266b959692d49fcce926daef2cfd9eecc19b07`，已对本地seal及五个代码/spec文件、synthetic-receipt计算文件身份hash并与seal/回执匹配。core为`47117ada2e0e301b1ac48b31ab8ffa0ec80194b68a416c21edb0852f0b899076`，合成回执为`dc34969c4b93d263aa2e720ee53a441f2019d9f380a9015f943391ad834659bb`。inputs/run与初审最终版不变。
- R1关闭：economic-protection-fix.diff显示fill新增risk_observe；仅terminal调用False，仍逐腿更新买卖数量/名义、cash、BTC、费用与日志。terminal整体前观察一次，全部腿结束后观察一次，不再在腿间复用未扣原深度估值。tests.py新增三档terminal fixture同时检查末现金/库存、峰值/回撤不变、三腿保留及会计分解闭合；33项回执报告该项PASS。
- R2关闭：core invariant新增独立累计买卖名义及量的C/Q精确恒等式，result实际调用invariant；有归因时非零identity_residual实际raise ArithmeticError。缺参考的原归因UNKNOWN仍不被伪造成0或额外盈利门槛。新增人为现金微小漂移及归因微小漂移两fixture验证拒绝，回执报告PASS。
- 已读preformal-amendment.json、修复diff、新spec、相关测试、新回执、seal相关字段、四份resource-prepare原件、prepare第3次stderr及当前completion。一次prepare失败确为旧depth不足fixture直接凭空赋inv，被新C/Q守恒guard拒绝；修后fixture同时设对应买入量/名义/费用/现金，保留缺深度UNKNOWN断言，没有放宽正式guard。失败日志/资源保留，当前prepare exit0，累计记录Owner CPU0.196066秒，加既定review借记60秒；不是正式重跑。
- 修复未改q、F/H提示、E/X规则、延迟、费用、共同窗口、风险门槛或输入映射；spec只补原子终端及既定守恒语义。input_identity_unchanged为amendment所记录，本人未重读110份输入实体或行情body重做QC。

静态及合成层准备闭合，不代表实际回放已完成。正式首失败/超帽即停，四情景两日门槛及UNKNOWN边界保持；未来即使正，也仅同样本内模型条件经济候选，不能归为个人获单、完整净利、容量或预测alpha的因果证明。未运行代码/测试/回放、未联网或读保护目录。actual model/effort/speed=UNKNOWN。
