# Bitstamp成交方向：供应商定义的工作映射可成立

2026-10-21 UTC14:02:44—14:03:08；1query＋1官方源码页面预算已止。实际model/effort UNKNOWN，规则沿派单；无Raw、行情、源码执行、模型或交易。

1. **映射源码已直接核到。** [官方src/mappers/bitstamp.ts](https://github.com/tardis-dev/tardis-node/blob/master/src/mappers/bitstamp.ts)页面显示219源码行。`bitstampTradesMapper`只处理live_trades频道的trade事件；网页L705精确代码为：

```ts
side: bitstampTrade.type === 0 ? 'buy' : 'sell',
```

2. **结合既有官方Data Types，足以形成有界工作解释。** 已保存`cross-market-paired-data-admission-20261021/root/data-types.native.txt`的L137明确trades.side是流动性taker/aggressor方向。因此按供应商定义：type=0 → canonical buy → 主动买方消耗ask，被动侧为sell/ask；type=1 → canonical sell → 主动卖方消耗bid，被动侧为buy/bid。源码实际将全部非0映射为sell，并非只检验type=1；不能据此宣称异常值已被验证或源枚举只含0/1。

3. **工作映射不等于自身成交或历史部署审计。** 本轮master未固定commit/发布日期，历史后台同一性UNKNOWN；这一限制不抹去公开供应商字段与映射的一致工作含义，也不要求无限追私有实现。它不能证明任一用户订单已排队/成交、trade与order事件原子对应，或trade在其他消息之前已经可知。未读行情、填充率或订单账，不补此类结论。

仅输出本side-source目录，未修改上一collector或其他Owner报告。Data Types来源：[官方规范](https://docs.tardis.dev/downloadable-csv-files/data-types.md)，本轮复用本日保存原文，没有新增读取该页。
