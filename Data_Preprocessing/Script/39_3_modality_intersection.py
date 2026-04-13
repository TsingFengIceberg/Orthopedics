import os
import pandas as pd

# ================= 配置路径 =================
temp_dir = '../Temp_data'
mapping_file = os.path.join(temp_dir, '37_Intersection_Image_Mapping.xlsx')

print("🚀 [39号] 启动多模态影像交集提取引擎 (宽容包含逻辑)...\n")

# ================= 1. 加载映射底座 =================
print("📂 正在加载 [37号] 纯净版影像映射表...")
df_mapping = pd.read_excel(mapping_file)
df_mapping['MODALITYID'] = df_mapping['MODALITYID'].astype(str).str.strip()
df_mapping['病历号'] = df_mapping['病历号'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# ================= 2. 定义清洗与模态提取函数 =================
def extract_valid_modality_ids(clean_file, unmatched_file, modality_type):
    clean_path = os.path.join(temp_dir, clean_file)
    unmatched_path = os.path.join(temp_dir, unmatched_file)
    
    if not os.path.exists(clean_path): return set()
        
    df_clean = pd.read_csv(clean_path, dtype=str)
    
    # 剔除 Unmatched 数据
    if os.path.exists(unmatched_path):
        df_unmatched = pd.read_csv(unmatched_path, dtype=str)
        invalid_ids = set(df_unmatched['Image_Data_ID'].dropna().str.strip())
        df_clean = df_clean[~df_clean['Image_Data_ID'].str.strip().isin(invalid_ids)]
        
    # 自动定位 Modality 列
    mod_col = [col for col in df_clean.columns if '(0008,0060)' in col.replace(' ', '') or 'Modality' in col][0]
    
    # 精确过滤
    if modality_type == 'CT':
        valid_df = df_clean[df_clean[mod_col].str.strip().str.upper() == 'CT']
    elif modality_type == 'MR':
        valid_df = df_clean[df_clean[mod_col].str.strip().str.upper() == 'MR']
    elif modality_type == 'XRay':
        valid_df = df_clean[df_clean[mod_col].str.strip().str.upper().isin(['DX', 'CR'])]
    else:
        valid_df = pd.DataFrame()
        
    return set(valid_df['Image_Data_ID'].dropna().str.strip())

# ================= 3. 提取三大模态的底层 MODALITYID =================
print("🔍 正在穿透解析底层 DICOM 元数据，提取有效模态...")
ct_ids = extract_valid_modality_ids('10_CT_Metadata_Clean.csv', '22_New_Unmatched_CT_Metadata_Full.csv', 'CT')
mr_ids = extract_valid_modality_ids('10_MR_Metadata_Clean.csv', '22_New_Unmatched_MR_Metadata_Full.csv', 'MR')
xray_ids = extract_valid_modality_ids('10_XRay_Metadata_Clean.csv', '22_New_Unmatched_XRay_Metadata_Full.csv', 'XRay')

def assign_modality_type(m_id):
    if m_id in ct_ids: return 'CT'
    if m_id in mr_ids: return 'MR'
    if m_id in xray_ids: return 'XRay'
    return 'Unknown' 

df_mapping['影像类型'] = df_mapping['MODALITYID'].apply(assign_modality_type)
df_mapping = df_mapping[df_mapping['影像类型'] != 'Unknown']

# ================= 4. 患者维度聚合 =================
print("🔄 正在将影像维度上卷至患者维度...")
df_patient_modality = df_mapping.groupby(['病历号', '影像类型'])['MODALITYID'].apply(lambda x: ', '.join(x)).unstack(fill_value='')

for col in ['CT', 'MR', 'XRay']:
    if col not in df_patient_modality.columns:
        df_patient_modality[col] = ''

# ================= 5. 集合论：7 种“包含逻辑”组合盘点 =================
print("\n" + "="*50)
print("📊 [多模态患者宽容包含盘点矩阵 (At-least Logic)]")
print("="*50)

# 🌟 新增：打印总计人数
total_patients = len(df_patient_modality)
print(f"👥 总计发现有效影像患者: {total_patients:,} 人\n")

# 布尔掩码
has_ct = df_patient_modality['CT'] != ''
has_mr = df_patient_modality['MR'] != ''
has_xray = df_patient_modality['XRay'] != ''

# ⚠️ 核心改变区：这里不再使用互斥的 `~` (非) 操作符
combinations = {
    # 1. 只要有单模态就算 (包含拥有更多模态的人)
    "Has_CT": has_ct,
    "Has_MR": has_mr,
    "Has_XRay": has_xray,
    
    # 2. 只要同时有双模态就算 (包含三模态大满贯的人)
    "Has_CT_and_MR": has_ct & has_mr,
    "Has_CT_and_XRay": has_ct & has_xray,
    "Has_MR_and_XRay": has_mr & has_xray,
    
    # 3. 三模态大满贯
    "Has_All_Three": has_ct & has_mr & has_xray
}

# ================= 6. 导出盘点结果 =================
print("💾 正在统计并保存各组合的映射表...\n")
for name, mask in combinations.items():
    df_subset = df_patient_modality[mask].copy()
    count = len(df_subset)
    
    print(f"  ♦ {name.ljust(20)} : {count:,} 人")
    
    if count > 0:
        df_subset = df_subset.reset_index()
        
        # 智能精简列：用户要什么组合，导出的表里就只给什么列的 MODALITYID
        # (比如要 Has_CT_and_MR，表里就只留 CT 和 MR 的文件夹名字，忽略 XRay)
        cols_to_keep = ['病历号']
        if 'CT' in name or 'All_Three' in name: cols_to_keep.append('CT')
        if 'MR' in name or 'All_Three' in name: cols_to_keep.append('MR')
        if 'XRay' in name or 'All_Three' in name: cols_to_keep.append('XRay')
        
        df_subset = df_subset[cols_to_keep]
        
        # 重命名
        rename_dict = {'CT': 'MODALITYID_CT', 'MR': 'MODALITYID_MR', 'XRay': 'MODALITYID_XRay'}
        df_subset.rename(columns=rename_dict, inplace=True)
        
        out_file = os.path.join(temp_dir, f'39_Patient_Modality_{name}.xlsx')
        df_subset.to_excel(out_file, index=False)

print("\n🎉 完美收官！7 种宽容包含逻辑的患者映射表已生成！")