# 文章与代码对应关系

文章主题：多示踪剂脑 PET 的标准化 SUVR 量化与 AI-assisted QC triage。

## 方法部分对应代码

| 文章模块 | 对应代码 |
|---|---|
| Cohort locking / scan list | 本地 `dataset_master_locked_*.xlsx`，不公开上传 |
| Tracer matching | `scripts/05_build_adni_roi_suvr_table.py` |
| SUVR extraction | `scripts/05_build_adni_roi_suvr_table.py` |
| Robust Z-score | `scripts/06_compute_robust_zscore_table.py` |
| Scan-level QC features | `scripts/07_generate_qc_features_table.py` |
| Summary table | `scripts/08_make_results_summary_table.py` |
| De-identified/local export | `scripts/09_make_deid_exports_table.py` |
| Figure scripts | `scripts/make_fig2_qc_trigger_breakdown.py`、`scripts/plot_fig3_compact_regional_robust_z_profiles.py` |

## README 中建议强调

- 这是 expert-in-the-loop QC triage，不是自动诊断模型。
- Robust Z-score 是基于 tracer-region 分布的 median/MAD。
- 输出的 `moderate_review` 和 `extreme_review` 是审阅优先级，不是医学结论。
- 真实 ADNI 数据需要用户自行按照 ADNI 权限下载，仓库只提供代码和合成示例。
