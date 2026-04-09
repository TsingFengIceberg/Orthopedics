import pandas as pd
import re
import os

# ================= 配置路径 =================
input_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"
output_dir = "../Temp_data"  # 直接输出到 Temp_data 目录下
os.makedirs(output_dir, exist_ok=True)
# ============================================

def is_private_tag(col_name):
    """判断是否为私有标签 (组号为奇数)"""
    match = re.search(r'\((\w{4}),', str(col_name))
    if match:
        try:
            return int(match.group(1), 16) % 2 != 0
        except:
            pass
    return False

print(f"📥 正在加载原始大宽表，请稍候...")
df = pd.read_csv(input_csv, low_memory=False)

# 自动定位 Modality 列
mod_col = [col for col in df.columns if '(0008, 0060)' in col.replace(' ', '') or 'Modality' in col][0]

# 划定三大核心模态子集 (直接丢弃 OT 等垃圾模态)
modality_filters = {
    "CT": df[df[mod_col] == 'CT'].copy(),
    "MR": df[df[mod_col] == 'MR'].copy(),
    "XRay": df[df[mod_col].isin(['DX', 'CR'])].copy()
}

fixed_cols = ["Image_Data_ID", "Image_Name"]

# 🎯 确定的终极阈值：保留非空率 >= 5% 的特征
tolerance_threshold = 0.05 

for mod_name, mod_df in modality_filters.items():
    print(f"\n================ [ {mod_name} 模态清洗 ] ================")
    
    # 1. 屠杀私有标签
    cols_to_drop = [c for c in mod_df.columns if is_private_tag(c)]
    mod_df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
    print(f"   🔪 已砍掉 {len(cols_to_drop)} 个厂商私有标签。")
    
    # 2. 剔除极度稀疏列 (保留非空率 >= 5% 的列)
    min_non_na = int(len(mod_df) * tolerance_threshold)
    feature_cols = [c for c in mod_df.columns if c not in fixed_cols]
    
    df_features = mod_df[feature_cols].dropna(thresh=min_non_na, axis=1)
    final_df = pd.concat([mod_df[fixed_cols], df_features], axis=1)
    print(f"   🧹 已清理空洞特征，保住了非空率 >= 5% 的黄金特征。")
    
    # 3. 导出最终表 (命名为 10_ 开头，直接保存在 Temp_data)
    out_path = os.path.join(output_dir, f"10_{mod_name}_Metadata_Clean.csv")
    final_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"   ✅ [{mod_name}] 完美收官！最终保留 {len(final_df.columns)} 个高质量特征。")
    print(f"   💾 已安全保存至: {out_path}")

print("\n🎉 三张纯净的元数据基准表生成完毕！")