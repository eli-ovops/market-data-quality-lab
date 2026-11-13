# 独立库存退出：准备完成，正式未开始

实现入口run.py，唯一路径`formal`；尚未启动或读取历史行情正文。32项人工合成通过。新core.py显式继承逐字保存的base_core.py；inputs.py与原纠错版逐字一致，prepare有实际hash guard。旧F0/H0只引用旧result，不重跑。完整差异complete-diff.patch；规范与版本来源spec.json；输入小身份/runtime/源与合成绑定preparation-seal.json。

新增实现：每buy fill FIFO lot，统一sell扣减；年龄1秒触发→撤两侧屏障δ→固定FIFO退出量及独立预留→再δ到达。退出锁期原grid/sign照记仅阻新提交；Q0于τ解锁且严格后继整秒恢复。退出同capture组共用有限25档预算，新capture组才重置；年龄/日终共同扣。已发送exit不被日终取消，未发屏障由终端接管。路径参考/深度不可识别则保留首UNKNOWN、现金/BTC/预留并冻结该路径；其他预定路径照报。完整现金/风险/归因分层；有BTC且风险参考已被exit消费则价格风险UNKNOWN；纯现金仍可知。新增增量日志含FIFO分配/lot余量、事务/发送冻结量及预留、深度reset及before-used-after、终端接管/阻断/UNKNOWN。

合成覆盖见synthetic-receipt.json逐项32 PASS：FIFO部分买卖、<q、两段延迟、发送后成熟下一批、冻结量、预留、Q0、缺参考/不足全量不部分执行、同组累计/新组重置、消费后风险、pending冲突取消、终端sent/unsent接管、不双卖、锁期grid/sign与日志证据。人工报价fixture原只有0时点，首轮因年龄>1s变陈旧而失败；原失败log/resource和旧tests均保留，修为人工0.5s更新序列后通过，没有历史结果择参。第二代进一步加边界的原源/receipt/seal保留history-prepare-v1及prior-v1文件，原资源没有复制进历史重复记账。

当前Python固定绝对解释器/3.12.14实际回执见synthetic/preparation-seal；正式也强校验同executable/version。32项全部是人工，无真实行情预演。准备CPU各resource按实测累计，另resource-auxiliary-debit对短小文本编辑/hash进程保守扣1CPU秒（不冒称实测），Root/Reviewer另预留150s；Owner上限450CPU，总600。线程1、RSS512MiB，Owner磁盘guard120MiB预留共享8MiB，截止16:01:37UTC；无付费/网络/数据/下载安装/模型/账户钱包交易。actual model/effort/speed UNKNOWN。

唯一formal须Root `RELEASED_ONE_FORMAL_ECONOMIC_UNIT`绑定当前seal且原件身份一致；排他formal-started先写，技术失败/超帽首STOP不重跑。仅必要适配及预正式合成已执行，正式、未来新规则与择优运行未执行。当前等待独立静态审阅及Root版本放行。
