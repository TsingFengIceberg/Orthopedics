import pandas as pd
import numpy as np
import os

# 你的大表路径
input_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"
# 输出的新版按模态独立的统计报告
output_summary = "../Temp_data/06_DICOM_Modality_Specific_Summary.xlsx"

print(f"📥 正在读取大宽表: {input_csv} (请稍候)...")
df = pd.read_csv(input_csv, low_memory=False)
print(f"✅ 读取成功！大表总尺寸: {df.shape[0]} 行, {df.shape[1]} 列")

# 1. 自动定位 Modality 列
modality_col = [col for col in df.columns if '(0008, 0060)' in col.replace(' ', '') or 'Modality' in col]
if not modality_col:
    raise ValueError("❌ 找不到模态列，请检查提取的宽表格式！")
modality_col = modality_col[0]
print(f"🏷️ 成功定位模态列: {modality_col}")

# 2. 划定三大核心模态的子集 (直接忽略 OT)
print("🔀 正在按模态拆分数据集...")
df_ct = df[df[modality_col] == 'CT']
df_mr = df[df[modality_col] == 'MR']
df_xray = df[df[modality_col].isin(['DX', 'CR'])]  # 将 DX 和 CR 合并为 X 光组

modality_groups = {
    "CT": df_ct,
    "MR": df_mr,
    "XRay": df_xray
}

# 3. 准备写入 Excel (支持多 Sheet)
print(f"💾 准备生成分模态统计报告: {output_summary}")
# 确保输出目录存在
os.makedirs(os.path.dirname(output_summary), exist_ok=True)

with pd.ExcelWriter(output_summary, engine='openpyxl') as writer:
    
    for mod_name, mod_df in modality_groups.items():
        total_rows = len(mod_df)
        print(f"\n🔍 正在分析 [{mod_name}] 组 (共 {total_rows} 个文件)...")
        
        if total_rows == 0:
            print(f"⚠️ [{mod_name}] 组没有数据，跳过分析。")
            continue
            
        summary_data = []
        
        # 遍历所有列计算当前模态下的统计特征
        for col in mod_df.columns:
            non_null_count = mod_df[col].notna().sum()
            missing_rate = (total_rows - non_null_count) / total_rows if total_rows > 0 else 1.0
            
            # 只有当非空数量 > 0 时才去取样本，否则填 NaN
            sample_val = mod_df[col].dropna().iloc[0] if non_null_count > 0 else np.nan
            
            col_info = {
                "Column_Name": col,
                "Non_Null_Count": non_null_count,
                "Missing_Rate": missing_rate, # 这里存小数，方便在 Excel 里排序或设置格式
                "Missing_Rate_Str": f"{missing_rate:.2%}", # 字符串格式仅供直观查看
                "Sample_Value": str(sample_val)[:50] if pd.notna(sample_val) else ""
            }
            summary_data.append(col_info)
            
        # 转换为 DataFrame
        summary_df = pd.DataFrame(summary_data)
        
        # 按照非空数量降序排序，也就是最完整的列排在最前面
        summary_df = summary_df.sort_values(by="Non_Null_Count", ascending=False)
        
        # 写入到对应的 Sheet 中
        summary_df.to_excel(writer, sheet_name=f"{mod_name}_Summary", index=False)
        print(f"✅ [{mod_name}] 组分析完毕并写入 Sheet: {mod_name}_Summary")

print("\n🎉 独立模态体检报告生成完毕！")
print(f"你可以将 {output_summary} 下载到本地，在 Excel 的不同 Sheet 中分别查阅 CT、MR 和 XRay 的专属特征分布了。")