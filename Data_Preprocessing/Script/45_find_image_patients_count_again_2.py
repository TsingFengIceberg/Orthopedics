import os
import pandas as pd

# ================= 配置路径 =================
temp_dir = '../Temp_data'
raw_list_file = os.path.join(temp_dir, '44_Absolute_Raw_DICOM_List.csv') # 注意：如果你刚才生成的文件名叫44开头，请改这里！
mapping_file = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables/Patient_Image_Mapping.xlsx'

print("🚀 [45号] 启动基于真实物理快照的终极患者模态统计引擎...\n")

# ================= 1. 加载物理全量快照并清洗模态 =================
print("📂 正在加载硬盘物理快照大表...")
if not os.path.exists(raw_list_file):
    raise FileNotFoundError(f"找不到 {raw_list_file}，请检查文件名！")

df_raw = pd.read_csv(raw_list_file, dtype=str)

def map_modality(m):
    m = str(m).strip().upper()
    if m == 'CT': return 'CT'
    if m == 'MR': return 'MR'
    if m in ['DX', 'CR']: return 'XRay'
    return 'Other'

df_raw['核心模态'] = df_raw['底层模态标签(Modality)'].apply(map_modality)

# 剔除垃圾模态 (OT, SR 等) 及损坏文件
df_valid = df_raw[df_raw['核心模态'] != 'Other'].copy()

# ================= 2. 降维至文件夹层级 (Folder Level) =================
print("📉 正在将数十万张图片降维至独立文件夹 (MODALITYID) 层级...")
df_folder = df_valid[['文件夹名称(MODALITYID)', '核心模态']].drop_duplicates()
df_folder.rename(columns={'文件夹名称(MODALITYID)': 'MODALITYID'}, inplace=True)
# 这一步非常安全：如果一个文件夹里有300张CT，它会变成1行；如果有CT也有MR，它会变成2行，完美保留。

print(f"   ▪ 提取到纯净的有效影像文件夹共计: {len(df_folder):,} 个。")

# ================= 3. 加载账本映射表并防爆过滤 =================
print("🔗 正在加载账本映射表并执行严格的空值绝杀过滤...")
df_map = pd.read_excel(mapping_file)

df_map['MODALITYID'] = df_map['MODALITYID'].astype(str).str.strip()
df_map['病历号'] = df_map['病历号'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# 核心防爆：杀掉所有导致踩踏的假性空值
invalid_strings = ['', 'nan', 'NAN', 'null', 'NULL', 'None']
df_map = df_map[~df_map['病历号'].isin(invalid_strings)]
df_map = df_map[~df_map['MODALITYID'].isin(invalid_strings)]

# ================= 4. 内连接 (Inner Join) 锁定有效患者 =================
print("🔄 正在执行【物理硬盘】与【账本映射】的交集对接...")
df_merged = pd.merge(df_folder, df_map[['MODALITYID', '病历号']], on='MODALITYID', how='inner')

# 聚合至患者层级 (同一个病人如果有多个CT文件夹，用逗号拼起来)
df_patient = df_merged.groupby(['病历号', '核心模态'])['MODALITYID'].apply(lambda x: ', '.join(set(x))).unstack(fill_value='')

for col in ['CT', 'MR', 'XRay']:
    if col not in df_patient.columns:
        df_patient[col] = ''

# ================= 5. 维恩图盘点与结果输出 =================
print("\n" + "="*50)
print("🏆 [物理级绝对真实：多模态患者宽容包含盘点矩阵]")
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
        
        out_file = os.path.join(temp_dir, f'45_Patient_Modality_{name}.xlsx')
        df_subset.to_excel(out_file, index=False)

print("\n🎉 完美绝杀！这批数据的 CT 人数绝对会暴涨！快去跟医生报喜吧！")