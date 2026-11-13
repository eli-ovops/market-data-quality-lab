# deep-orderbook：公开代码、数据、权重及个人复用许可

读取UTC：2026-10-21 08:30:36—08:31:55。固定HEAD为bbc3debfb34b2ccb27db75e2e5ae027406f040d4，提交时间2020-10-08T13:51:40Z。本Owner首个HEAD请求在协调消息前已发出，计1次；之后复用model/tree.json完整tree（truncated=false），没有重复取tree。另读5个固定文本blob，累计6次公开读取，预算用尽。

1. **软件确实公开，个人复用有MIT正文依据。** [固定LICENSE](https://github.com/Globe-Research/deep-orderbook/blob/bbc3debfb34b2ccb27db75e2e5ae027406f040d4/LICENSE)为MIT、Copyright 2019 Globe Research，准许软件使用、复制及修改等，须保留版权及许可声明，且无担保。完整tree有10个notebook与LICENSE/README/.gitignore/paper/main.tex，没有独立数据文件或预训练权重blob；不能把“代码公开”写成完整模型工件已公开。MIT许可软件及相应文档，不自动扩展到外部行情权利。

2. **存在精确数据下载链接，但本轮没有取得数据原件。** [固定CoinBase.ipynb](https://github.com/Globe-Research/deep-orderbook/blob/bbc3debfb34b2ccb27db75e2e5ae027406f040d4/CoinBase.ipynb)首个代码cell给出[Dropbox coinbase_btc_usd.7z](https://www.dropbox.com/sh/w3qagq2ze9noxon/AACE6f4nkBAJaJEc7Nbf2nhla/coinbase_btc_usd.7z?dl=0)。这是精确公开代码引用，区别于Data_Filtering.ipynb的本地Data路径及/content下parquet；但未请求归档链接、未下载/解压，当前可达性、内容/日期完整性、hash和数据个人复用许可均UNKNOWN。不得因论文声称提供数据而认定实际原件已验。Coinbase行情不因本研究名字而套Tardis合同，也不能因此自动认定自由使用。

3. **当前只能准入纸面/源码静态研究，非严格复现。** [固定README](https://github.com/Globe-Research/deep-orderbook/blob/bbc3debfb34b2ccb27db75e2e5ae027406f040d4/README.md)写2秒walk-forward 76%，仅外链SSRN3704098，无数据/权重说明；这不能自行绑定arXiv2010.01241v1的71%结果或某份notebook输出。标签/训练版本绑定由model Owner负责。本Owner未执行来源代码、未加载pickle/权重或任何行情数据，未安装/登录/交易；个人源码研究许可与数据/结果复现准入分别保留。

本地原件：HEAD-commit.json、LICENSE.txt、README.md.txt、.gitignore.txt；两notebook仅保存代码cell文本，未保存其输出。text-source-receipts.json保留blob SHA与API原件URL，并核Git blob SHA匹配。完整tree归model Owner，未改其文件。

model Owner分工补证（本Owner未重复取blob）：WalkForwardV2/Walkthrough的TCN输入引用GCS bucket_l2_snapshot/l2_snapshot_100ms.csv，经storage.Client读取；CNN_Deeplearning_walkforward引用gs://bucket_l2_snapshot/l2_snapshot_100ms.csv，不能据此证明公共可达。CNN引用本地models/model_resnet_walkforward.h5并上传到bucket对象model_resnet_walkforward；TCN检查点为本地model_resnet_walkforward_tcn_actual.h5及model_resnet_walkforward_tcn.h5。这些是输入/保存路径引用，均不是本轮已取得的公开权重原件；没有读取所引用凭证文件或请求GCS对象。
