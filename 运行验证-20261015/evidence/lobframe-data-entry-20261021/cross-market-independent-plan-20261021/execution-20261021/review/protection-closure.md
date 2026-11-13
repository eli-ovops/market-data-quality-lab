# Stage0两项保护：整改闭合

审阅UTC日期2026-10-21；精确起止时分UNKNOWN。实际model / effort UNKNOWN。**accept=true；must_fix=[]。** 原preformal-review.md两项均关闭；无新增正式前问题。由Root在既有完整单元授权内决定一次正式放行，不需用户重复授权。

## 对应整改

1. 新增bind_frozen_inputs固定比较date/path/expected_rows/expected_sha256，检查封存actual_sha256与expected一致，并从封存记录返回身份。formal先完成此绑定，再按封存hash核实际文件；共享旧回执与输入共同漂移也不能改变本次身份。diff仅改变formal入口绑定，不改groups、as-of、深度/费用或正空间判断。
2. Budget构造进入try且先置None；初始化异常进入正式首STOP写入，只有预算对象成功创建才尝试finish。既有STOP/正式标识的拒绝仍在前，首STOP不覆盖。新增测试临时替换OUT为owner/synthetic-formal-budget-...后模拟失败，并恢复OUT/Budget/argv；没有在实际stage0目录模拟失败。

## 证据与身份

实际本地hash核对：

- stage0.py：`05795585da12a56af7cc6c7d47a31a9053e4963674ea968292f7a0a84247bcaf`。
- preflight-seal.json：`91275c145ade058d238c2c7ab9d318ec2e2341e0fe297559202e1efd29d3e8ee`。
- protection-amendment.json：`c68dd954d0f5062a3d6a43791d51dc0593237956c1b08cf3a548da708429038b`；diff：`2033f26186c27fcbb4dae3ae295dc08002f5e4c948e800826678cadeb353a72b`。
- 新test-stage0.py：`fcb410e1364270bedae628d4718a8f41381dffba38f39f63b8018c68a35ec1ba`；11项synthetic-tests-amended.json：`6284c08cd62210e575a405e48c0195b68b3f8ce731bb2853c207eee479bd9799`。原件声明real_inputs_opened=0、real_economics=0，测试source支持此范围。
- preflight.json未改：`99e5d4863681f0f29d50fe3b2ea625b315c5c6a34b32a8a76994c733df0c79d6`；旧seal副本仍为`5946a8a52ae02380dc74e73fb5369b0460962b244119c21a15674dfcfc3d0b14`。新seal绑定新代码/测试/11项结果、原preflight/parameters/输入，引用旧seal与amendment路径；本review另绑定amendment实际hash。

已读amendment对相关函数未变的逐项记录，与完整修订diff一致；复用原18项经济/时序fixture及真实身份QC，不要求重复运行。目录文件名核对仅见隔离owner测试路径的terminal-stop，真实stage0未见formal-started/terminal-stop或正式输出；不冒称本终审独立检查进程。amendment-budget记录累计17.616838832s含原10s保守预留、无resource重复副本；新增测试峰RSS24,444,928B。本轮不重新计费/计算资源总额。

仅阅读protection-amendment.diff/json、synthetic-tests-amended.json、amendment-budget.json、新seal必要头尾及指定文件hash/标识；原任务单及已审规范复用。不重审全实现，不重跑合成/正式/CRC/QC或经济，不读缓存行情/数组/权重，不联网/账户/交易。只新增review/本文件，不改其他原件，旧A/B STOP不变。
