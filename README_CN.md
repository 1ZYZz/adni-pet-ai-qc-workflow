# ADNI 多示踪剂 PET SUVR 与 AI-assisted QC 工作流

这是给投稿文章配套的公开 GitHub 代码仓库模板。它整理了表格版 PET ROI/SUVR 工作流：

1. 检查 ADNI PET ROI/SUVR 表字段；
2. 按锁定 scan list 匹配 FDG、Amyloid、Tau PET；
3. 提取统一 long-format SUVR 表；
4. 计算 tracer-region robust Z-score；
5. 生成 scan-level QC triage 标签；
6. 输出本地审阅用表格和图。

## 公开原则

这个仓库默认只公开：

- 代码；
- 说明文档；
- 合成示例数据；
- 论文级汇总结果。

不要公开上传：

- 原始 ADNI CSV；
- `dataset_master_locked_*.xlsx`；
- 逐扫描、逐 ROI 的真实 SUVR/Z-score/QC 表；
- 投稿前 `.docx`、`.pdf`、submission package；
- 任何含内部 ID、扫描日期、路径或 subject/scan 清单的文件。

## 快速运行合成示例

macOS/Linux：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_table_workflow.sh
```

Windows：

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
RUN_TABLE_WORKFLOW_WINDOWS.bat
```

## 用你自己的授权 ADNI 数据运行

建议把真实数据放在仓库外，或者放在 `.gitignore` 已忽略的 `private_data/` 目录：

```text
private_data/
├── dataset_master_locked_YYYY-MM-DD.xlsx
└── adni_tables/
    ├── UCBERKELEYFDG_*.csv
    ├── UCBERKELEY_AMY_*.csv
    └── UCBERKELEY_TAU_*.csv
```

运行：

```bash
./run_table_workflow.sh private_data/dataset_master_locked_YYYY-MM-DD.xlsx private_data/adni_tables outputs
```

更多 GitHub 公开步骤见：

```text
docs/GITHUB_PUBLICATION_GUIDE_CN.md
```
