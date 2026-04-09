import pandas as pd

# 配置你的大表路径
input_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"

print("📥 正在极速扫描大表的表头...")
# 先读前两行，精准定位模态列的具体名称
df_sample = pd.read_csv(input_csv, nrows=2)
modality_col = [col for col in df_sample.columns if '0008,0060' in col.replace(' ', '') or 'Modality' in col]

if modality_col:
    col_name = modality_col[0]
    print(f"✅ 成功定位模态列: {col_name}")
    print(f"🚀 正在极速统计 {col_name} 列的全量数据...\n")
    
    # 利用 usecols 只读取这一列，速度极快且极其省内存
    df_modality = pd.read_csv(input_csv, usecols=[col_name], low_memory=False)
    
    # 统计各个模态的具体频次
    modality_counts = df_modality[col_name].value_counts()
    
    print("📊 【数据集真实模态全景图】")
    print("=" * 40)
    print(f"{'模态 (Modality)':<20} | {'文件数量 (Count)':<15}")
    print("-" * 40)
    
    total_files = 0
    for mod, count in modality_counts.items():
        print(f"{str(mod):<22} | {count:<15}")
        total_files += count
        
    print("=" * 40)
    print(f"总计文件数: {total_files}")
    
else:
    print("❌ 未在表格中找到包含 '0008,0060' 或 'Modality' 的列，请检查提取的宽表格式。")