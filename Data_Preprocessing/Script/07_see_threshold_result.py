import pandas as pd
import re

# 配置你的大宽表路径
input_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"

def is_private_tag(col_name):
    match = re.search(r'\((\w{4}),', str(col_name))
    if match:
        try:
            return int(match.group(1), 16) % 2 != 0
        except:
            pass
    return False

print(f"📥 正在加载原始大宽表，请稍候...")
df = pd.read_csv(input_csv, low_memory=False)

mod_col = [col for col in df.columns if '(0008, 0060)' in col.replace(' ', '') or 'Modality' in col][0]

modality_filters = {
    "CT": df[df[mod_col] == 'CT'],
    "MR": df[df[mod_col] == 'MR'],
    "XRay": df[df[mod_col].isin(['DX', 'CR'])]
}

for mod_name, mod_df in modality_filters.items():
    print(f"\n================ [ {mod_name} 模态分析 ] ================")
    total_rows = len(mod_df)
    
    # 1. 过滤本模态完全为空的列 (比如 CT 表里全空的 MR 专属字段)
    active_cols = mod_df.dropna(how='all', axis=1).columns
    mod_active_df = mod_df[active_cols]
    
    # 2. 杀掉私有标签，得到公共纯净池
    public_cols = [c for c in mod_active_df.columns if not is_private_tag(c)]
    public_df = mod_active_df[public_cols]
    
    total_public = len(public_cols) - 2 # 减去ID和Name这两列
    
    # 3. 计算 0.1 和 0.5 阈值保留情况
    thresh_10 = int(total_rows * 0.10)
    thresh_50 = int(total_rows * 0.50)
    
    # 计算每一列的非空数量
    non_null_counts = public_df.notna().sum()
    
    # 获取不同阈值下保留的列名
    cols_10 = non_null_counts[non_null_counts >= thresh_10].index.tolist()
    cols_50 = non_null_counts[non_null_counts >= thresh_50].index.tolist()
    
    # 计算差异的列（那些非空率在 10% 到 50% 之间的尴尬列）
    diff_cols = set(cols_10) - set(cols_50)
    
    pct_10 = (len(cols_10) - 2) / total_public * 100
    pct_50 = (len(cols_50) - 2) / total_public * 100
    
    print(f"有效公共特征总数: {total_public} 列")
    print(f"阈值 0.1 (非空≥10%): 保留 {len(cols_10)-2} 列 ({pct_10:.1f}%)")
    print(f"阈值 0.5 (非空≥50%): 保留 {len(cols_50)-2} 列 ({pct_50:.1f}%)")
    print(f"两者差值: 差了 {len(diff_cols)} 列\n")
    
    if diff_cols:
        print(f"👀 这 {len(diff_cols)} 个处于 10%~50% 边缘地带的字段分别是：")
        print("-" * 50)
        for col in sorted(diff_cols):
            # 去除固定的那两列
            if col in ["Image_Data_ID", "Image_Name"]: continue
            count = non_null_counts[col]
            missing_rate = (total_rows - count) / total_rows
            print(f"  - {col}: 缺失率 {missing_rate:.2%} (非空数: {count})")
        print("-" * 50)