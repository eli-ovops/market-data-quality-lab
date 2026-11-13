# XTX2019参赛者方法：目标、因果调用及评价边界

结论：该仓库是参赛者的部分数据准备/特征工程材料，不能证明官方评分定义、最终参赛模型、获奖名次或实际交易赚钱。87 ticks不是已核固定墙钟秒数；README的自写R²公式不能当作一般预测R²。只保留方法线索，不替代Root与数据Owner的官方来源核查。

来源身份：候选[dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data](https://github.com/dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data)；固定commit `74493c54c452938cbd3c152eef2a8ca1187952ed`，author/committer日期均2020-05-27T05:15:31Z，tree `cceed694236fac95b32b993a1d238ab23eb76cce`，truncated=false。完整tree仅README和两个notebook，没有最终训练/预测程序、模型或原始CSV。作者在README自称与2019年9月XTX/Correlation One挑战的个人提交有关，不能从仓库名称升格为XTX官方或生产系统。

本轮公共读取5/5：gh code search(target，0hit不推不存在)、commit/HEAD元数据、完整固定tree、README blob、Data Preparation in Q blob。gh auth仅沿用现有只读状态，不取凭证内容/变更认证。notebook仅JSON惰性抽取source，不执行其中q/Python/命令，不读取保存的行情数组outputs。没有下载CSV/权重/pickle、克隆、安装、训练、回测、账户或交易；旧STOP保持。

## 1. 标签只披露为87个事件步后的mid变化，原公式/单位/边界与秒数均未确定

[固定README L19–27](https://github.com/dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data/blob/74493c54c452938cbd3c152eef2a8ca1187952ed/README.md#L19)称训练约300万ticks，每行含买卖各前14档价格及数量，另给target y，为87 ticks内/后的midprice change。没有在这份自述中给出差分vs比例、端点vs平滑、价格单位、样本边界及缺口处理，不能自行补成美元差、bp或两秒收益。

[Data Preparation in Q零基cell10–11，原JSON L156–165](https://github.com/dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data/blob/74493c54c452938cbd3c152eef2a8ca1187952ed/Data%20Preparation%20in%20Q.ipynb#L156)明确说没有timestamp，以行号充当time，并执行time:i。故87 ticks是有序行/事件距离，不是87秒，也没有依据转换为其他固定秒数。即使比赛要求逐行实时处理，也不提供每行现实时间间隔。

该notebook计算midprice=(askRate0+bidRate0)/2，但没有生成y的源码；target由比赛数据预给。其读取文件的source不证明实际目标对齐，原数据也不在本轮读取范围。另一份Market Depth and Order Messages未读取，不能把未读范围说成已穷尽全仓标签逻辑。

## 2. 公开了部分历史特征准备，但没有足以认证的最终逐行调用链或非重叠划分

[README L17](https://github.com/dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data/blob/74493c54c452938cbd3c152eef2a8ca1187952ed/README.md#L17)称Random Forest on non-overlapping data为其winning model，且模型选择/调参以后再上传。这里只能解释为其自称最终选用方案；没有名次/获奖证据，不能译成比赛冠军模型。固定tree未列对应最终程序，无法确认RF参数、特征列、非重叠间距是否≥87、训练/验证按时间划分、跨边界标签清除或最终私有集实际调用日志。

已读q源码包括零值填空、当前mid/spread/队列加权价、窗口5/15/45/87/180/360的msum均值、当前与lag差、各档数量和imbalance、档间距离。该部分source没有显式从未来行取值作为历史特征；但这不能替代对未公开最终特征选择/预测入口的检查，也未执行或验证其依赖lib.q。

源码有具体局限：[cell29，L424](https://github.com/dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data/blob/74493c54c452938cbd3c152eef2a8ca1187952ed/Data%20Preparation%20in%20Q.ipynb#L424)名为moving volatility/std的f_std_t与前一cell moving average一样使用(msum)/窗口长度，未实现标准差。该静态事实说明列名不能代替实际计算定义；没有证据证明该列进入最终参赛模型或影响官方成绩。

README特别警告past y不能作为下一tick预测输入，这是因果限制的正面自述：y包含未来结果，上一行y在下一行时不当然已知。已读notebook载入整表、最后保存整个特征表，没有展示最终X去除y/其他未来列的选择，也没有逐行predict接口/状态更新时间规则。因此不能证明已经违规使用y，同样也不能认证最终程序满足该警告。完整先后调用时序为UNKNOWN。

## 3. 私有评分只是参赛者陈述；自写R²表达式不可靠，也没有从评分到成交扣费的记录

[README L29–30](https://github.com/dushiyu/Mid-price-Prediction-Based-on-High-Frequency-Data/blob/74493c54c452938cbd3c152eef2a8ca1187952ed/README.md#L29)称提交特征构造代码和模型，在private data上实时测试、按R²排序。但其公式是Σ(yhat−ybar)²/Σ(y−ybar)²，缺少预测残差项。一般样本外预测的决定系数应为1−Σ(y−yhat)²/Σ(y−ybar)²；只有额外正交分解等特定条件下，解释平方和之比才可与它对应，不能对任意预测盲用。还未明确它是否本意为相关系数平方或其他主办方定义。

因此此处不将参赛者公式升级为官方评分口径，也不擅自纠正后声称已知比赛实评分数。该仓库未给可绑定的private成绩数值、逐行预测/真值、评测日志或排名原件；官方分数定义由Root/数据Owner独立核验，此Owner不重复读取官方仓库或旧站。

其模型<256MB、云机60分钟处理60000行的限制同样只按README记录，不视为本轮核实的官方实时约束或现实订单延迟。预测任务的吞吐/模型大小限制不是订单确认、排队和实际成交证据。

在已读README/source及固定tree范围没有完整实际订单→成交→退出→手续费/返佣账。不能说作者个人从未记录/从未交易；只能说当前材料没有提供这一层，也没有可据以给出扣成本净收益的结果。比赛预测成绩即使真实较高，也不能自动填补成交价格、队列、持仓和费用链。

## 收口

可保留：参赛者将有序盘口事件、历史特征与实时预测约束结合的方法线索，以及“不应把past future-target当即时输入”的明确提醒。未取得：精确目标定义/墙钟映射、最终无泄漏逐行入口/划分、官方评分与私有运行身份、完整真实交易账。上述UNKNOWN不证明方法无效，亦不构成后续模型或交易运行许可。

本报告只写method目录，没有改其他Owner文件。目标gpt-6.1-sol/medium，实际model/effort UNKNOWN；规则PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4沿用。付款/安装/来源代码执行/行情数组读取/模型/回测/账户交易0。
