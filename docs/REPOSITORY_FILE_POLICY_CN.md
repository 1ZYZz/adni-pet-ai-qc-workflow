# GitHub 公开文件策略

## 建议公开上传

- `scripts/`：你自己写的处理脚本。
- `requirements.txt`：Python 依赖。
- `README.md`、`docs/`：运行说明、方法说明、数据使用提醒。
- `examples/synthetic/`：合成示例数据，不能是真实 ADNI 数据。
- `results_public/Table1_metrics_for_summary.csv`：仅包含论文级汇总指标时可考虑上传。
- `CITATION.cff`：论文发表后补 DOI。

## 不建议公开上传

- `adni_tables/` 里的 UC Berkeley ADNI 原始 CSV。
- `dataset_master_locked_*.xlsx`，因为它包含锁定 subject/scan 清单、日期、内部 ID 等。
- `outputs/SUVR_region_table.csv`、`outputs/Zscore_table.csv`、`outputs/QC_features.csv` 等逐扫描、逐 ROI 的真实结果。
- `outputs/deid_exports/*_deid.csv`：虽然去掉了一些内部字段，但仍是个体级派生数据，公开前需要确认数据使用协议。
- 投稿前的 `.docx`、`.pdf`、投稿包 zip，特别是双盲投稿时。

## 推荐公开策略

1. GitHub 公开：代码 + 合成示例数据 + 运行说明。
2. 真实 ADNI 数据：只保存在本地或受控服务器。
3. 论文结果：在 manuscript 中报告汇总统计和图；仓库中只保留能够复现结果的代码。
4. 论文接收后：再补充 DOI、正式引用格式和 release tag。
