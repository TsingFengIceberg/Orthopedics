import pandas as pd
import numpy as np

# 你的大表路径
input_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"
output_summary = "../Temp_data/04_DICOM_Column_Summary.xlsx"

print(f"📥 正在读取大表: {input_csv} (请稍候，100MB大概需要几秒钟)...")
df = pd.read_csv(input_csv, low_memory=False)

print(f"✅ 读取成功！数据集大小: {df.shape[0]} 行, {df.shape[1]} 列")

# 准备统计列表
summary_data = []

total_rows = len(df)

# 如果你的数据里包含了 Modality 字段，我们可以提取出来看一下
# 先找找哪个列是 Modality
modality_col = [col for col in df.columns if '(0008, 0060)' in col or 'Modality' in col]
if modality_col:
    modality_col = modality_col[0]
    print(f"🏷️ 发现模态列: {modality_col}")
    modalities = df[modality_col].dropna().unique().tolist()
    print(f"📊 数据集包含的模态: {modalities}")
else:
    modality_col = None

print("🔍 正在计算各列的缺失率和统计特征...")
for col in df.columns:
    non_null_count = df[col].notna().sum()
    missing_rate = (total_rows - non_null_count) / total_rows
    
    # 统计有多少个不同的值 (nunique 比较耗时，这里简单处理)
    # 取一个非空的样本值看看长什么样
    sample_val = df[col].dropna().iloc[0] if non_null_count > 0 else np.nan
    
    col_info = {
        "Column_Name": col,
        "Non_Null_Count": non_null_count,
        "Missing_Rate": f"{missing_rate:.2%}",
        "Sample_Value": str(sample_val)[:50] # 只截取前50个字符作为预览
    }
    
    # 如果有 Modality，我们统计一下这个字段在各个模态下的非空数量
    if modality_col and col != modality_col:
        for mod in modalities:
            mod_mask = df[modality_col] == mod
            mod_non_null = df.loc[mod_mask, col].notna().sum()
            col_info[f"{mod}_Non_Null_Count"] = mod_non_null
            
    summary_data.append(col_info)

# 转换为 DataFrame 并导出
summary_df = pd.DataFrame(summary_data)

# 按照缺失率从小到大排序（最完整的列排在最前面）
summary_df = summary_df.sort_values(by="Non_Null_Count", ascending=False)

print(f"💾 正在导出统计报告: {output_summary}")
summary_df.to_excel(output_summary, index=False)
print("🎉 报告生成完毕！这个 Excel 文件通常只有几十 KB。")