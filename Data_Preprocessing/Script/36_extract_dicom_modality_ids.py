import os
import pandas as pd

# ================= 配置路径 =================
dicom_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS'
temp_dir = '../Temp_data'
os.makedirs(temp_dir, exist_ok=True)
out_file_36 = os.path.join(temp_dir, '36_Physical_Modality_IDs.xlsx')

print("🚀 [36号] 启动物理影像目录盘点...")

if not os.path.exists(dicom_dir):
    raise FileNotFoundError(f"⚠️ 找不到 DICOM 根目录: {dicom_dir}")

# 1. 遍历并获取所有子文件夹名称 (即物理存在的 MODALITYID)
physical_modality_ids = []
for folder_name in os.listdir(dicom_dir):
    folder_path = os.path.join(dicom_dir, folder_name)
    if os.path.isdir(folder_path):
        physical_modality_ids.append(folder_name.strip())

# 2. 转换为 DataFrame 并去重（理论上文件夹名不可能重复，但保险起见）
df_physical = pd.DataFrame({'MODALITYID_物理': physical_modality_ids})
df_physical = df_physical.drop_duplicates()

print(f"📊 盘点完毕！在硬盘上共发现 {len(df_physical)} 个独立的 DICOM 影像文件夹 (MODALITYID)。")

# 3. 保存
df_physical.to_excel(out_file_36, index=False)
print(f"💾 物理 ID 列表已保存至: {out_file_36}\n")