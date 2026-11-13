# Making Multiple Markets：maker返佣条件有限核验

读取UTC：2026-10-21 08:00:01—08:01:03。2次公开search、4个页面，均为教程作者文档或官方公告；未运行模型、回测、费用情景，未登录或询问账户。本报告不是使用该场所的建议。

1. **来源身份修正：本案例唯一目标是[canonical教程](https://hftbacktest.readthedocs.io/en/latest/tutorials/Making%20Multiple%20Markets.html)，与本Owner实际读取的[hft.readthedocs.io旧站](https://hft.readthedocs.io/en/latest/tutorials/Making%20Multiple%20Markets.html)不是同一固定版本。** 旧站L18及L228的maker_fee=-0.00005、taker_fee=0.0007仅作为另一版本参考，不能固定本例源码或结果身份。canonical的.trading_value_fee_model(-0.00005,0.0007)由Root及records Owner本轮原页与固定ipynb核验支持，本Owner未直接读取canonical，不冒充独立核验。0.005%=0.5bp；负maker费率是返佣设定，但未做费用贡献拆分或无返佣对照，其对本例利润贡献UNKNOWN。旧站返回文本只有公告标题，本Owner未取得canonical精确出链；下列2022/2023公告均不能证明与canonical精确链接绑定。

2. **最高返佣不是$5,000普通账户自动可得。** [官方2022-07-20公告](https://www.binance.com/en/support/announcement/detail/5d3a662d3ace4132a95e77f6ab0f5422)L17—61：标准自2022-07-25生效、返佣2022-08-02更新。USDT-M最高档-0.005%要求周maker份额2.50%或报价排名前10%；申请入口要求30日期货成交量≥1亿BUSD等值或现货≥2000万，需审核，新申请宽限只给0.003%，按周复核，自成交不计份额。本金不等于成交量或持续达标资格。表中BUSD-M另列-0.014%，故教程的“最高0.005%”不能泛化成全部合约的最高值。

3. **2023样本期与2026不能混用。** [2023-06-01公告](https://www.binance.com/en/support/announcement/detail/41e7931982274a24a48eb545222cf531)官方搜索索引列6月5日标准/6月13日返佣生效，最高档为1.50%总maker份额，或剔除BTC/ETH后份额1.50%，或报价前10%；但直接读取跳到公告总页，未取得该文正文，不改路径重取。因此这是2023年7月历史条件的有限线索，实际账户/各合约适用未认证。[2023-10-09公告](https://www.binance.com/en/support/announcement/detail/891da3b2fb6842fb875e40d1f4463fc5)正文可读，10月23日起改为三档、仍有周复核及变更保留，进一步证明计划会变。未完整核2026现行版本，当前最高返佣及个人资格UNKNOWN；不提供刷量建议。历史返佣条件足以限制教程对普通个人的可复制性，但不能直接据此断言教程亏损或策略本身无效。

完整来源日期、实际正文/索引读取差异与UNKNOWN见source-receipt.json。官方历史公告只是类似返佣计划的条件证据，不能升级为canonical的准确出链、源码版本或实际账户费率认证。仅写本fees目录，未改任何其他Owner原件。

修正回执：保留旧站实际读取事实，明确两个站点不能混作同一固定版本；没有新增外部读取、源码执行或费用重算。首次文档修正命令因stdin编码错误在解析阶段停止，未写文件；改用apply_patch及ASCII脚本完成本目录修正，没有重试外部来源。
