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

# 定义要测试的阈值阶梯: 0, 0.05, 0.10 ... 0.50
thresholds = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

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
    print(f"有效公共特征总数: {total_public} 列 (此为阈值 0，只要有1个值就算)\n")
    
    # 计算每一列的非空数量
    non_null_counts = public_df.notna().sum()
    
    # 用于记录上一个阶梯的列，方便对比
    previous_retained_cols = None
    previous_thresh = None
    
    for t in thresholds:
        # 当 t=0 时，意味着非空数 > 0；其他情况意味着非空数 >= 总行数*t
        if t == 0.0:
            current_cols = set(non_null_counts[non_null_counts > 0].index.tolist())
        else:
            thresh_val = int(total_rows * t)
            current_cols = set(non_null_counts[non_null_counts >= thresh_val].index.tolist())
        
        # 排除掉固定的两列，算真实的特征数
        feature_cols = {c for c in current_cols if c not in ["Image_Data_ID", "Image_Name"]}
        retained_count = len(feature_cols)
        pct = (retained_count / total_public * 100) if total_public > 0 else 0
        
        print(f"► 阈值 {t:.2f} (非空≥{t*100:g}%): 保留 {retained_count} 列 (占 {pct:.1f}%)")
        
        # 如果不是第一步，就对比一下被这一轮阈值“干掉”的字段
        if previous_retained_cols is not None:
            dropped_cols = previous_retained_cols - feature_cols
            
            if dropped_cols:
                print(f"  ⚠️ 相比阈值 {previous_thresh:.2f}，被淘汰的 {len(dropped_cols)} 个字段：")
                for col in sorted(dropped_cols):
                    count = non_null_counts[col]
                    missing_rate = (total_rows - count) / total_rows
                    print(f"      - {col}: 缺失率 {missing_rate:.2%} (非空数: {count})")
            else:
                print(f"  ✅ 相比阈值 {previous_thresh:.2f}，没有字段被淘汰。")
                
        print("-" * 60)
        
        previous_retained_cols = feature_cols
        previous_thresh = t