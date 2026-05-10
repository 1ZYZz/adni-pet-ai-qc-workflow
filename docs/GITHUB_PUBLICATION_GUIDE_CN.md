# 一步一步公开到 GitHub

下面假设你的本地文件夹名是：

```bash
adni-pet-ai-qc-workflow-public
```

## 第 1 步：最后检查不要上传的文件

进入项目目录：

```bash
cd adni-pet-ai-qc-workflow-public
```

检查文件：

```bash
git status
find . -maxdepth 3 -type f
```

确认没有这些内容：

```text
adni_tables/
dataset_master_locked_*.xlsx
UCBERKELEY*.csv
UCSFFSX*.csv
outputs/SUVR_region_table.csv
outputs/Zscore_table.csv
outputs/QC_features.csv
*.docx
*.pdf
```

## 第 2 步：本地测试代码能运行

安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows：

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

运行合成示例：

```bash
./run_table_workflow.sh
```

Windows：

```cmd
RUN_TABLE_WORKFLOW_WINDOWS.bat
```

## 第 3 步：初始化 Git

```bash
git init
git add .
git status
git commit -m "Initial public release of ADNI PET QC workflow"
```

## 第 4 步：在 GitHub 新建仓库

建议仓库名：

```text
adni-pet-ai-qc-workflow
```

建议先选择 **Private**，检查无误后再改成 **Public**。投稿前如果期刊或会议要求双盲，不要公开带作者信息、投稿稿件、致谢信息或真实数据结果的内容。

## 第 5 步：连接远程仓库

把下面命令里的 `OWNER` 和 `REPOSITORY` 换成你的 GitHub 用户名和仓库名：

```bash
git branch -M main
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

## 第 6 步：确认网页显示正常

打开 GitHub 仓库页面，重点检查：

- README 是否能清楚说明项目用途。
- `examples/synthetic/` 是否只包含假数据。
- 是否没有真实 ADNI 表、逐扫描结果表、投稿 docx/pdf。
- `CITATION.cff` 中的 `repository-code` 是否已改成真实 GitHub 地址。
- `LICENSE_TODO.txt` 是否已替换为正式 `LICENSE`。

## 第 7 步：公开仓库

如果一开始建的是 Private：

1. 打开 GitHub 仓库。
2. 进入 **Settings**。
3. 滚到 **Danger Zone**。
4. 选择 **Change repository visibility**。
5. 改成 **Public**。

公开前再做一次检查：

```bash
git ls-files
```

只要看到真实 ADNI 数据、锁定 cohort 表、投稿稿件，就先不要公开。

## 第 8 步：论文发表后补充

论文接收后建议更新：

- `README.md` 中加入论文 DOI。
- `CITATION.cff` 中加入 DOI 和正式发表年份。
- 创建一个 GitHub release，例如 `v1.0.0`。
- 在论文 Data/Code Availability 中写明 GitHub 地址。
