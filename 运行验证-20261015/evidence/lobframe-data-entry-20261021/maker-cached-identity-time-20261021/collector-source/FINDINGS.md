# 官方Bitstamp collector源码语义：本轮未证L3快照锚定

UTC读取窗口2026-10-21 13:57:47—13:58:23；2query＋3source读取已止。实际model/effort UNKNOWN；仅官方仓库源码文本，未执行、安装或调用行情接口；未重复Raw、拒绝Bitstamp详情或overview路径。

1. **本轮实际读到的快照实现是L2/group=1，不能当成live_orders的group=2证明。** [官方src/realtimefeeds/bitstamp.ts](https://github.com/tardis-dev/tardis-node/blob/master/src/realtimefeeds/bitstamp.ts)页面显示117源码行，代码本体可读。`BitstampWebSocketRealTimeFeed.provideManualSnapshots`只选择`diff_order_book`过滤器，请求`order_book/{symbol}?group=1`；将返回data包装为snapshot、对应diff_order_book频道、generated:true，压入manualSnapshotsBuffer。此方法没有live_orders专用分支、group=2或[price,amount,id]元组解析。该静态客户端分支不是供应商历史后台全部实现：L3历史snapshot如何生成、是否有其他内部版本仍UNKNOWN，不能从本方法推断不存在L3记录。

2. **缓冲与输出顺序有代码证据，精确事件锚点未证。** [官方src/realtimefeeds/realtimefeed.ts](https://github.com/tardis-dev/tardis-node/blob/master/src/realtimefeeds/realtimefeed.ts)的`RealTimeFeedBase`在连接建立后等待订阅确认及首数据消息，再调用provideManualSnapshots；处理循环先yield收到的消息，再排出manualSnapshotsBuffer并清空。断连会清缓冲。已读构造的snapshot没有额外事件ID/sequence锚字段；“存在缓冲”不等于快照与此前live_orders的原子切点已证明，也不等于重放不会重复/漏事件。源data可包含什么锚字段未在本方法校验，仍UNKNOWN。

3. **localTimestamp及历史部署身份仍UNKNOWN。** 已读Bitstamp包装与base输出链没有取得localTimestamp赋值点，不能写成HTTP请求前、响应完成时或WS底层收包瞬间；也不能把稍后yield时刻当数据状态时刻。trade.type到主动side映射文件本轮未读，UNKNOWN。两个master页面均未返回可固定commit/发布日期；base先显示553源码行，后find显示614，说明本轮动态返回不完全一致，不能作为同一不可变源码快照或2026年7—9月后台运行版本证明。

源码定位（工具网页行号，非仓库源码行号）：Bitstamp页面L564—607为manual snapshot方法；base第二返回L1646—1710为WS消息/快照缓冲输出，L1947—1962为首数据等待与fetch调用。没有保存整份源码或宣称源码hash封存。本轮只回答上述已读边界，不重复缓存ID/time检查，不修改其他Owner材料。
