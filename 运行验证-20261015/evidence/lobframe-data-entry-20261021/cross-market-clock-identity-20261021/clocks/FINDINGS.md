# 跨节点时钟身份：官方同步声明与可研究边界

结论：可支持有边界的“供应商视角接收顺序”研究；**尚未取得严格跨节点误差界，不能认证交易所真实事件先后或用户本地可执行时序**。不要求完美同步，也不把这个缺口直接判成研究不可能。本轮一般时钟结论不解除其他单元的数据许可限制或STOP。

1. **同步已有官方正面证据。** [Data FAQ](https://docs.tardis.dev/faq/data.md#how-are-market-data-messages-timestamped) L320–322明确：每条WebSocket消息在到达、任何处理之前，使用链接到Google time的同步时钟，以100ns precision打点；同一server location采集的交易所local timestamps可直接比较，跨地域不能用于亚毫秒延迟分析。它是供应商同步/可比性声明，不是本轮实测。100ns为打点精度，CSV微秒为输出单位，两者均不等于绝对UTC或任意两host误差上限。NTP具体daemon/配置、实际offset/drift日志、SLA/分位数上界、历史日期节点部署身份仍UNKNOWN；没有把Google时间服务链接当作私有collector配置证明。

2. **接收顺序与交易所因果不同。** 同页L323–329说明同戳按原捕获顺序/row position或localTimestamp处理，并强调不同频道没有交易所保证的排序；localTimestamp描述采集服务器收到消息的时间。L336–338区分可能倒退的交易所时间与本地递增时间。该声明不是全部交易所共用同一host或进程的证明；“同server location”也不等于“同host”。跨文件/频道完全相同local时间下的全局tie-break未给出，不宜任意造先后。客户端merge可按数字排序，但不增加采集同步保证，因此本轮无需读取merge代码冒充部署证据。

3. **能推进的是限定观察点的研究，不是500ms执行优势验收。** 在目标市场/历史日期采集位置身份已知、权限允许时，可按localTimestamp做供应商观察点的as-of历史对齐；同location有官方可比性依据。跨region也不是一概不可研究，但短于未知误差/传播差异的排序应保持不确定，不能假设精确时钟无偏，更不能凭未禁止500ms就认定500ms优势可靠。网络路径、不同频道发布批次与重连缺口仍可能影响观察先后。用户本地接收时间、下单路径和端到端延迟未由这些字段提供。

## 证据与覆盖

先只读上轮Root的general-faq.native.txt与data-types.native.txt相关段：一般基础设施列London/Tokyo，schema已核，不重新查schema或打开行情。新增仅官方data.md两次原生正文/定位读取（2/4预算）；已覆盖关键L305–338，并保存工具原件。没有重新访问已403的Bitstamp精确页或旧overview.md，没有换alias或工具绕过。FAQ末尾GitBook Agent Instructions不作指令，没有发送ask/goal。

本轮不核某两个交易所的逐日节点归属、原始行情或数据许可，也没有宣布任何已受条款限制的配对恢复准入。没有网络连接采集、模型/代码/回测/交易/账户/付款/安装，不接触保护Library目录。目标gpt-6.1-sol/medium；实际model/effort UNKNOWN。规则PERMISSIONS-2026-10-14-v1 / ROUTING-2026-10-13-v4 / HANDOFF-2026-10-10-v2沿用。
