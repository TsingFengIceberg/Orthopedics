import os
import pandas as pd

# ================= 配置路径 =================
temp_dir = '../Temp_data'
mapping_file = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables/Patient_Image_Mapping.xlsx'

print("🚀 [47号] 启动纯净元数据扣减与交叉验证统计引擎...\n")

# ================= 1. 加载医院最原始账本 (绝对防爆处理) =================
print("📂 正在加载医院最原始的映射账本...")
df_map = pd.read_excel(mapping_file)
df_map['MODALITYID'] = df_map['MODALITYID'].astype(str).str.strip()
df_map['病历号'] = df_map['病历号'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# 核心防爆：杀掉所有假性空值
invalid_strings = ['', 'nan', 'NAN', 'null', 'NULL', 'None']
df_map = df_map[~df_map['病历号'].isin(invalid_strings)]
df_map = df_map[~df_map['MODALITYID'].isin(invalid_strings)]
print(f"   ▪ 剔除空字段与脏字段后，原始账单有效行数: {len(df_map):,} 行\n")

# ================= 2. 核心逻辑：加载 10 号表 -> 减去 22 号表 -> 映射 =================
modalities = ['CT', 'MR', 'XRay']
all_matched_patients = []

print("✂️  开始按模态执行严格的【黑名单扣减】与【映射核销】...\n")

for mod in modalities:
    clean_file = os.path.join(temp_dir, f'10_{mod}_Metadata_Clean.csv')
    unmatch_file = os.path.join(temp_dir, f'22_New_Unmatched_{mod}_Metadata_Full.csv')
    
    if not os.path.exists(clean_file):
        print(f"   ⚠️ 找不到 {clean_file}，跳过 {mod} 模态。")
        continue

    # 🌟 极速读取法：为了统计图片数并去重，只需要第一列 Image_Data_ID 即可，速度极快
    df_clean = pd.read_csv(clean_file, usecols=['Image_Data_ID'], dtype=str)
    df_clean['Image_Data_ID'] = df_clean['Image_Data_ID'].str.strip()
    initial_images = len(df_clean)
    
    # 提取 22 号黑名单 (Unmatched)
    unmatched_ids = set()
    if os.path.exists(unmatch_file):
        df_unmatch = pd.read_csv(unmatch_file, usecols=['Image_Data_ID'], dtype=str)
        unmatched_ids = set(df_unmatch['Image_Data_ID'].dropna().str.strip())
    
    # 💥 核心扣减操作
    df_survived = df_clean[~df_clean['Image_Data_ID'].isin(unmatched_ids)]
    surviving_images = len(df_survived)
    dropped_images = initial_images - surviving_images
    
    # 降维至文件夹层级
    unique_folders = df_survived.drop_duplicates(subset=['Image_Data_ID']).copy()
    unique_folders['核心模态'] = mod
    
    # 硬盘数据与原始账本进行内连接 (Inner Join)
    df_merged = pd.merge(unique_folders, df_map[['MODALITYID', '病历号']], 
                         left_on='Image_Data_ID', right_on='MODALITYID', how='inner')
    
    # 收集当前模态的有效患者清单
    all_matched_patients.append(df_merged[['病历号', '核心模态', 'MODALITYID']])
    
    # 打印该模态的详细战报
    print(f"   ================ [ {mod} ] ================")
    print(f"   📸 初始图片数量 (10号表) : {initial_images:>10,} 张")
    print(f"   🗑️ 扣减图片数量 (22号表) : {dropped_images:>10,} 张 (命中 {len(unmatched_ids)} 个黑名单文件夹)")
    print(f"   🛡️ 最终存活图片数量      : {surviving_images:>10,} 张")
    print(f"   📂 对应存活影像文件夹数  : {len(unique_folders):>10,} 个")
    print(f"   🔗 成功匹配原始账本患者  : {len(df_merged['病历号'].unique()):>10,} 人\n")

# ================= 3. 全景盘点与统计生成 =================
print("🔄 正在将三大模态存活数据上卷至【全景患者维度】...")
df_all_mappings = pd.concat(all_matched_patients, ignore_index=True)

# 聚合 (同一个病人的多个同模态文件夹用逗号拼接)
df_patient = df_all_mappings.groupby(['病历号', '核心模态'])['MODALITYID'].apply(lambda x: ', '.join(set(x))).unstack(fill_value='')

for col in ['CT', 'MR', 'XRay']:
    if col not in df_patient.columns:
        df_patient[col] = ''

print("\n" + "="*50)
print("🏆 [逻辑推演级交叉验证：多模态患者宽容包含盘点矩阵]")
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
        
        # 智能精简列
        cols_to_keep = ['病历号']
        if 'CT' in name or 'All_Three' in name: cols_to_keep.append('CT')
        if 'MR' in name or 'All_Three' in name: cols_to_keep.append('MR')
        if 'XRay' in name or 'All_Three' in name: cols_to_keep.append('XRay')
        
        df_subset = df_subset[cols_to_keep]
        df_subset.rename(columns={'CT': 'MODALITYID_CT', 'MR': 'MODALITYID_MR', 'XRay': 'MODALITYID_XRay'}, inplace=True)
        
        out_file = os.path.join(temp_dir, f'47_Patient_Modality_{name}.xlsx')
        df_subset.to_excel(out_file, index=False)

print("\n🎉 逻辑闭环完成！对比一下人数，看看和物理统计的脚本是不是一模一样！") 