import os
import pandas as pd
import pydicom
from tqdm import tqdm  # 用于显示酷炫的进度条

# ================= 配置路径 =================
raw_dicom_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS'
mapping_file = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables/Patient_Image_Mapping.xlsx'
temp_dir = '../Temp_data'
os.makedirs(temp_dir, exist_ok=True)

out_dicom_list = os.path.join(temp_dir, '43_1_Raw_DICOM_File_Level_List.csv')
out_stats = os.path.join(temp_dir, '43_2_New_Modality_Intersection_Stats.txt')

print("🚀 [43号] 启动基于物理底层的 DICOM 全量扫描与映射统计引擎...\n")

# ================= 第一步：物理硬盘全量扫描 (一张一行) =================
print("🔍 正在深入硬盘物理目录，逐张解析 DICOM 协议头 (速度极快模式)...")

records = []
modality_folders = [d for d in os.listdir(raw_dicom_dir) if os.path.isdir(os.path.join(raw_dicom_dir, d))]

# 遍历每一个 MODALITYID 文件夹
for mod_id in tqdm(modality_folders, desc="扫描进度"):
    folder_path = os.path.join(raw_dicom_dir, mod_id)
    
    # 遍历文件夹里的每一张图片
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        
        # 跳过子文件夹，只读文件
        if not os.path.isfile(file_path): continue
            
        try:
            # 🌟 核心魔法：stop_before_pixels=True，只读文字标签不读图片，极速！
            ds = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
            # 获取 (0008, 0060) Modality 标签
            modality = ds.get('Modality', 'UNKNOWN')
            
            # 添加到总表： [MODALITYID, 文件名, 原始模态]
            records.append([mod_id, file_name, modality])
        except Exception as e:
            # 万一混入了非 dicom 文件 (如 .DS_Store, .txt) 直接跳过
            pass

# 构建文件级大表 (一张一行)
df_all_dicoms = pd.DataFrame(records, columns=['MODALITYID', 'FileName', 'Raw_Modality'])
df_all_dicoms['Raw_Modality'] = df_all_dicoms['Raw_Modality'].str.strip().str.upper()

print(f"\n✅ 物理扫描完毕！共读取了 {len(df_all_dicoms):,} 张有效 DICOM 图片。")

# ================= 划定三大核心模态子集 (直接丢弃 OT 等垃圾模态) =================
def map_to_core_modality(m):
    if m == 'CT': return 'CT'
    if m == 'MR': return 'MR'
    if m in ['DX', 'CR']: return 'XRay'
    return 'Other' # 将被舍弃

df_all_dicoms['核心模态'] = df_all_dicoms['Raw_Modality'].apply(map_to_core_modality)

# 舍弃垃圾模态
df_valid_dicoms = df_all_dicoms[df_all_dicoms['核心模态'] != 'Other'].copy()

# 保存第一张表：全量明细大表 (由于行数极大，必须存CSV)
print(f"💾 正在保存第一张表：全量 DICOM 模态明细表 (共 {len(df_valid_dicoms):,} 行)...")
df_valid_dicoms.to_csv(out_dicom_list, index=False, encoding='utf-8-sig')


# ================= 第二步：与映射表交集并降维至患者层级 =================
print("\n🔗 正在加载账本映射表，执行交叉去重验证...")
df_map = pd.read_excel(mapping_file)
df_map['MODALITYID'] = df_map['MODALITYID'].astype(str).str.strip()
df_map['病历号'] = df_map['病历号'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# 1. 影像侧降维 (Folder Level)：一个文件夹里可能有300张CT，我们只要知道这个文件夹是CT就行
df_folder_level = df_valid_dicoms[['MODALITYID', '核心模态']].drop_duplicates()
print(f"   ▪ 降维后，共有 {len(df_folder_level):,} 个独立的纯净影像文件夹。")

# 2. 内连接 (Inner Join) 映射：既在硬盘上有，又在账本里有病历号的，才是真数据
df_merged = pd.merge(df_folder_level, df_map[['MODALITYID', '病历号']], on='MODALITYID', how='inner')
print(f"   ▪ 完美映射后，共有 {len(df_merged):,} 个有效的、带有病历号的影像任务。")

# 3. 聚合至患者层级 (Patient Level)
# 同一个病人可能有多个CT，把它们的MODALITYID拼起来
df_patient_modality = df_merged.groupby(['病历号', '核心模态'])['MODALITYID'].apply(lambda x: ', '.join(set(x))).unstack(fill_value='')

for col in ['CT', 'MR', 'XRay']:
    if col not in df_patient_modality.columns:
        df_patient_modality[col] = ''

# ================= 第三步：39号逻辑统计 (宽容包含逻辑 At-least) =================
print("\n" + "="*50)
print("📊 [基于物理底层的多模态患者宽容包含盘点矩阵]")
print("="*50)

total_patients = len(df_patient_modality)
print(f"👥 总计发现绝对有效影像患者: {total_patients:,} 人\n")

has_ct = df_patient_modality['CT'] != ''
has_mr = df_patient_modality['MR'] != ''
has_xray = df_patient_modality['XRay'] != ''

combinations = {
    "Has_CT": has_ct,
    "Has_MR": has_mr,
    "Has_XRay": has_xray,
    "Has_CT_and_MR": has_ct & has_mr,
    "Has_CT_and_XRay": has_ct & has_xray,
    "Has_MR_and_XRay": has_mr & has_xray,
    "Has_All_Three": has_ct & has_mr & has_xray
}

# 打印并导出各组合映射表
for name, mask in combinations.items():
    df_subset = df_patient_modality[mask].copy()
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
        
        out_file = os.path.join(temp_dir, f'43_Patient_Modality_{name}.xlsx')
        df_subset.to_excel(out_file, index=False)

print("\n🎉 物理溯源核对完毕！这版数据是不可被辩驳的终极真相！")