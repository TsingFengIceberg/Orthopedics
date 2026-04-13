import os
import pandas as pd

# ================= 配置路径 =================
temp_dir = '../Temp_data'
mapping_file = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables/Patient_Image_Mapping.xlsx'

print("🚀 [48号] 启动【切片级】精准扣减与交叉验证统计引擎...\n")

# ================= 1. 加载医院最原始账本 =================
print("📂 正在加载医院最原始的映射账本...")
df_map = pd.read_excel(mapping_file)
df_map['MODALITYID'] = df_map['MODALITYID'].astype(str).str.strip()
df_map['病历号'] = df_map['病历号'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

invalid_strings = ['', 'nan', 'NAN', 'null', 'NULL', 'None']
df_map = df_map[~df_map['病历号'].isin(invalid_strings)]
df_map = df_map[~df_map['MODALITYID'].isin(invalid_strings)]
print(f"   ▪ 剔除空字段与脏字段后，原始账单有效行数: {len(df_map):,} 行\n")

# ================= 2. 核心逻辑：切片级扣减 -> 降维映射 =================
modalities = ['CT', 'MR', 'XRay']
all_matched_patients = []

print("✂️  开始按模态执行【切片级】精准黑名单扣减...\n")

for mod in modalities:
    clean_file = os.path.join(temp_dir, f'10_{mod}_Metadata_Clean.csv')
    unmatch_file = os.path.join(temp_dir, f'22_New_Unmatched_{mod}_Metadata_Full.csv')
    
    if not os.path.exists(clean_file):
        continue

    # 🌟 核心改变 1：同时读取 文件夹ID 和 图片文件名
    df_clean = pd.read_csv(clean_file, usecols=['Image_Data_ID', 'Image_Name'], dtype=str)
    
    # 构造唯一主键 (UID)：文件夹名/文件名
    df_clean['UID'] = df_clean['Image_Data_ID'].str.strip() + "/" + df_clean['Image_Name'].str.strip()
    initial_images = len(df_clean)
    
    # 提取 22 号黑名单 (同样构造 UID)
    unmatched_uids = set()
    if os.path.exists(unmatch_file):
        df_unmatch = pd.read_csv(unmatch_file, usecols=['Image_Data_ID', 'Image_Name'], dtype=str)
        df_unmatch['UID'] = df_unmatch['Image_Data_ID'].str.strip() + "/" + df_unmatch['Image_Name'].str.strip()
        unmatched_uids = set(df_unmatch['UID'].dropna())
    
    # 💥 核心改变 2：切片级精确扣减 (只删坏切片，绝不连坐文件夹)
    df_survived = df_clean[~df_clean['UID'].isin(unmatched_uids)].copy()
    
    surviving_images = len(df_survived)
    dropped_images = initial_images - surviving_images
    
    # 降维至文件夹层级 (只要这个文件夹还有幸存的切片，文件夹就活下来了！)
    unique_folders = df_survived.drop_duplicates(subset=['Image_Data_ID'])[['Image_Data_ID']].copy()
    unique_folders['核心模态'] = mod
    
    # 与原始账本进行内连接 (Inner Join)
    df_merged = pd.merge(unique_folders, df_map[['MODALITYID', '病历号']], 
                         left_on='Image_Data_ID', right_on='MODALITYID', how='inner')
    
    all_matched_patients.append(df_merged[['病历号', '核心模态', 'MODALITYID']])
    
    # 打印该模态的详细战报
    print(f"   ================ [ {mod} ] ================")
    print(f"   📸 初始切片数量 (10号表) : {initial_images:>10,} 张")
    print(f"   🗑️ 精准剔除切片 (22号表) : {dropped_images:>10,} 张 (命中黑名单切片)")
    print(f"   🛡️ 最终存活切片数量      : {surviving_images:>10,} 张")
    print(f"   📂 幸存有效影像文件夹数  : {len(unique_folders):>10,} 个")
    print(f"   🔗 成功匹配原始账本患者  : {len(df_merged['病历号'].unique()):>10,} 人\n")

# ================= 3. 全景盘点与统计生成 =================
print("🔄 正在将三大模态存活数据上卷至【全景患者维度】...")
df_all_mappings = pd.concat(all_matched_patients, ignore_index=True)

df_patient = df_all_mappings.groupby(['病历号', '核心模态'])['MODALITYID'].apply(lambda x: ', '.join(set(x))).unstack(fill_value='')

for col in ['CT', 'MR', 'XRay']:
    if col not in df_patient.columns:
        df_patient[col] = ''

print("\n" + "="*50)
print("🏆 [切片级精确验证：多模态患者宽容包含盘点矩阵]")
print("="*50)

total_patients = len(df_patient)
print(f"👥 总计发现绝对有效影像患者: {total_patients:,} 人\n")

has_ct = df_patient['CT'] != ''
has_mr = df_patient['MR'] != ''
has_xray = df_patient['XRay'] != ''

combinations = {
    "Has_CT": has_ct,
    "Has_MR": has_mr,
    "Has_XRay": has_xray,
    "Has_CT_and_MR": has_ct & has_mr,
    "Has_CT_and_XRay": has_ct & has_xray,
    "Has_MR_and_XRay": has_mr & has_xray,
    "Has_All_Three": has_ct & has_mr & has_xray
}

print("💾 正在导出 7 种黄金子集映射表...\n")
for name, mask in combinations.items():
    df_subset = df_patient[mask].copy()
    count = len(df_subset)
    
    print(f"  ♦ {name.ljust(20)} : {count:,} 人")
    
    if count > 0:
        df_subset = df_subset.reset_index()
        
        cols_to_keep = ['病历号']
        if 'CT' in name or 'All_Three' in name: cols_to_keep.append('CT')
        if 'MR' in name or 'All_Three' in name: cols_to_keep.append('MR')
        if 'XRay' in name or 'All_Three' in name: cols_to_keep.append('XRay')
        
        df_subset = df_subset[cols_to_keep]
        df_subset.rename(columns={'CT': 'MODALITYID_CT', 'MR': 'MODALITYID_MR', 'XRay': 'MODALITYID_XRay'}, inplace=True)
        
        out_file = os.path.join(temp_dir, f'48_Patient_Modality_{name}.xlsx')
        df_subset.to_excel(out_file, index=False)

print("\n🎉 逻辑彻底闭环！你亲自完成了从【连坐】到【精确制导】的数据架构升级！")