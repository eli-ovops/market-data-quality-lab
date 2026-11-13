# Globe 两秒预测：模型与评估准入静态核验

结论：固定作者仓库可以提供TCN研究入口，但不能将其现有notebook视为论文71%结果的无歧义复现，更不能将71%或README76%当作净盈利证据。以下只作三项会改变研究决策的发现，不开发、不运行。

身份与范围：论文为[arXiv2010.01241v1](https://arxiv.org/html/2010.01241v1)，2020-10-03；作者指向Globe-Research/deep-orderbook。源码固定commit `bbc3debfb34b2ccb27db75e2e5ae027406f040d4`（本Owner取自官方code search结果与该commit完整tree，是否当前HEAD由data Owner独立记录）。已读notebook完整source cells：WalkForwardV2 19cells、Walkthrough 20cells、CNN_Deeplearning_walkforward 38cells。未执行source或读取其行情/预测数组outputs；仅保存notebook原JSON并惰性抽取source。固定版本与论文产生各表的实际运行身份仍UNKNOWN，不能用notebook文件名或保存outputs证明运行链同一。

公开读取6/6：code search、固定tree、论文HTML、WalkForwardV2 blob、CNN_Deeplearning_walkforward blob、Walkthrough blob。README复用数据Owner已存文本，没有重复联网。仅通过已登录gh官方API与正常arXiv页面；无安装、行情下载、模型加载或交易，旧A等STOP保持。

## 1. 71%总体accuracy低于同表全Stable基准；方向指标有信息但分母不同，76%另列

[论文§3.1 Figure2表](https://arxiv.org/html/2010.01241v1#S3.SS1)的test support为Down 61,142、Stable 350,499、Up 53,759，共465,400。因此同一表上总预测Stable的总体accuracy为350499/465400 = **75.311345%**，高于论文headline和该表约71%，差约4.31个百分点。这只表明该总体accuracy未胜同分母多数类基准；不能把“没胜多数类accuracy”扩写成“完全没有方向信息”。

表中Down recall .61、Up recall .66的分母分别为真实Down和真实Up数量；precision .42/.40的分母分别为预测Down/Up数量。把它们称“61%/66%方向准确率”会混淆recall与precision。论文用这两个recall支持方向预测，不能换成下单胜率或成本后收益。表内Avg recall .71为总体/加权recall，不是三类macro recall。

固定README文字称76%walk-forward accuracy；论文Appendix B Table1也有约76%的另一classification report，Down/Stable/Up recall约.76/.77/.75，但该表没有support，无法建立与465,400单同一分母、同一下采样或同一split。故分别登记71%主walk-forward表、76%附录表和README76%，不择优、不平均、不合并。

论文说9天100ms Coinbase BTCUSD，2019年6月12–20日；训练窗口1–7天、测试后续1天并walk forward，主方向结果为7天训练/后1天测试。alpha经exhaustive search选定，但搜索/深度/训练天数等选择的独立验证集及最终未触碰测试段没有明确绑定。仅凭“walk-forward”名义不能证明所有模型选择都与测试隔离。

## 2. 代码alpha数值相同而标签尺度不同，并有一行对齐和类别命名差异

[论文§2.1](https://arxiv.org/html/2010.01241v1#S2.SS1)定义原始best ask/bid的midprice p；m−为p[t−19]至p[t]均值，m+为p[t+1]至p[t+20]均值。m−>m+·(1+.002)记+1，m−<m+·(1−.002)记−1，否则0。目标是两段平滑mid均值的相对变化分类；.002在原始价格上为20bp量级，既不是未来两秒末点价格，也不是实际可成交收益。

三份已读notebook均先执行normalise_data_per_day，再把l2_norm传给generate_y(alpha=.002)。以[WalkForwardV2 cell6–9](https://github.com/Globe-Research/deep-orderbook/blob/bbc3debfb34b2ccb27db75e2e5ae027406f040d4/WalkForwardV2.ipynb#L332)为主：每列按前一整日均值/样本方差标准化，标签mid由标准化a1、b1取平均；所以其.002不是原始美元mid上的20bp。减去均值后再做比例门槛不保持原始价格比例判别，a1/b1逐列缩放也不一定共用一个尺度；不能因alpha字面相同称目标相同。daily标准化的前日统计本身在次日已知；本轮未发现其使用当日全日统计回灌当日输入，但原数据连续性与日分桶实际对齐未读行情核验。

generate_y内部shift范围−20…19，m_b用0…19，m_a用−20…−1，确实是过去含当前20行与未来20行。函数默认alpha=10e−5（.0001），实际上述cell显式覆盖为.002；k虽为参数，drop/mean范围硬编码20，不能认定任意k参数生效。

手算输入对齐：令q为样本序号、原l2_norm行号从0计，preX去首末20行后，X[q]为原行[20+q,119+q]共100行；y丢首20行再丢100行，对应标签中心原行t=120+q。因此最后输入行为t−1，标签中心为下一行t；未来均值涵盖t+1…t+20。若每行严格100ms，它们距最后输入行为0.2…2.1秒，另有未纳入输入的中心t。此对齐不是把未来标签送进X，但也不是“最后输入行当t”的精确两秒定义。

代码将signed标签+1再做y+=1映到类别2，而TCN绘图ticklabels把类别2命名Up、0命名Down；从上述不等式看，过去均值较大/未来较小时得到+1。存在数字标签与方向名对照不一致，不能据此直接宣判论文表实际方向已颠倒，因为论文结果与当前notebook的同一运行链未被证明。

完整40列顺序没有在这些训练cells显式选择，D=40并未在generate_X切列，输入直接df_snapshot.to_numpy()；只能确认TCN要求100×40，不能猜数据已按某个通用LOB顺序排列，也不能自动将原始50档/200列直接输入。

## 3. 已读TCN调用链复用test作训练控制；下采样与walk-forward实现也未同论文绑定

[WalkForwardV2 cell14–15](https://github.com/Globe-Research/deep-orderbook/blob/bbc3debfb34b2ccb27db75e2e5ae027406f040d4/WalkForwardV2.ipynb#L889)明确fit(validation_data=(X_test,y_test))，val_loss用于EarlyStopping、ReduceLROnPlateau和最佳checkpoint，随后m.predict(X_test)。[Walkthrough cell14–15](https://github.com/Globe-Research/deep-orderbook/blob/bbc3debfb34b2ccb27db75e2e5ae027406f040d4/Walkthrough.ipynb#L851)相同。test不通过梯度直接拟合，不等于独立测试：其标签影响训练时长和学习率/选择，这条静态调用链不能提供未参与训练控制的测试成绩。论文是否另有真正独立程序为UNKNOWN，不以此推断其全部结果失效。

这两份TCN notebook只定义balance_classes函数，source没有实际调用下采样，而使用训练标签compute_class_weight('balanced')；论文说随机移除过量Stable，4,219,932变1,681,407。类权重与删除样本不是同一处理。CNN_Deeplearning_walkforward cell10的下采样及随机train/validation split整块位于三引号字符串内，当前source不会执行；若人为重新启用，balance_classes会把所有较大类别削到最小类，不仅删除Stable。不得把停用块当作已生效，也不能依赖旧notebook内存状态说明当前source完整可复现。

三个notebook的X_index均取l2_norm[20:-120]，对应窗口开始行而不是标签中心行；按它统计最后一天长度再切X/y。由上一项手算可知，样本真实标签中心晚100行，未来标签最远晚120行。因此切分按窗口起点日期时，末尾训练窗口/标签可延伸入名义test日；100ms连续情形量级约10–12秒。没有purge/embargo。相邻样本窗口重叠本身不证明预测看未来，但边界并未保证训练标签严格止于测试日开始之前。

已读三份训练notebook都只显示一次末日切分，未见跨1–7天训练长度/多个测试日的walk-forward循环；CNN版本还是另一个ResNet/SAME卷积结构，不能当论文TCN唯一实现。WalkForwardV2使用TCN+Dense3，dropout=.4、dilations=[1,2,4,8,16,32,64]、BN、Adam .01；Walkthrough为默认TCN参数、dropout=.2、Adam .001。二者与论文完全逐层/依赖版本对应均UNKNOWN，未读取或执行keras-tcn实现去补默认值。

## 收口与待核

本轮可确定：同表多数类baseline比较、三份固定source的调用/索引事实，以及论文与source之间的明确差异。不能确定：哪份notebook/依赖版本/真实数据产生各论文表，真实下采样分布、原始数据40列、测试独立性是否由未读脚本另行实现，以及任何扣费用优势。剩余notebook没有为读全而追加预算；图内和PDF数值视觉核验、许可及原始数据/权重可达性由Root/数据Owner负责。没有读取GCS/Dropbox数据或凭证文件，不声称XTX生产模型。

本轮不建议按现有notebook直接进入训练；先将其列为“作者开源研究材料，但当前标签与评估调用链未满足干净复现实验准入”的证据。该处分不是新运行许可，旧STOP不变。

目标gpt-6.1-sol/medium，实际model/effort UNKNOWN；规则PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4。
