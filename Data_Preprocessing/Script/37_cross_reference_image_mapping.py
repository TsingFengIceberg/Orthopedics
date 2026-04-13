import os
import pandas as pd

# ================= 配置路径 =================
raw_tables_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'
temp_dir = '../Temp_data'

physical_file = os.path.join(temp_dir, '36_Physical_Modality_IDs.xlsx')
mapping_file = os.path.join(raw_tables_dir, 'Patient_Image_Mapping.xlsx')

out_intersection = os.path.join(temp_dir, '37_Intersection_Image_Mapping.xlsx')
out_physical_only = os.path.join(temp_dir, '37_Physical_Only_Modality_IDs.xlsx')
out_mapping_only = os.path.join(temp_dir, '37_Mapping_Only_Modality_IDs.xlsx')

print("🚀 [37号] 启动影像映射双向审计...")

# 1. 加载数据，强制转换为字符串并清理首尾空格，防止类型错位
df_phys = pd.read_excel(physical_file)
set_phys = set(df_phys['MODALITYID_物理'].astype(str).str.strip())

df_map = pd.read_excel(mapping_file)
# 清洗 Mapping 表里的 MODALITYID
df_map['MODALITYID_Clean'] = df_map['MODALITYID'].astype(str).str.strip()
set_map = set(df_map['MODALITYID_Clean'])

# 2. 集合运算 (Set Operations)
intersection_ids = set_phys.intersection(set_map)
phys_only_ids = set_phys - set_map
map_only_ids = set_map - set_phys

print(f"🔍 [审计结果]")
print(f"   ✅ 两边都有的 (完美交集) : {len(intersection_ids)} 个")
print(f"   👻 硬盘有，但账本里没记录的 (孤儿影像) : {len(phys_only_ids)} 个")
print(f"   📄 账本里有，但硬盘上没找到的 (影像丢失) : {len(map_only_ids)} 个")

# 3. 构建输出表
# 3.1 完美的交集映射表 (保留账本的原始完整信息，只筛出合法的行)
df_intersection = df_map[df_map['MODALITYID_Clean'].isin(intersection_ids)].copy()
df_intersection = df_intersection.drop(columns=['MODALITYID_Clean']) # 删掉辅助列

# 3.2 物理特有表 & 映射特有表
df_phys_only = pd.DataFrame({'MODALITYID': list(phys_only_ids)})
df_map_only = df_map[df_map['MODALITYID_Clean'].isin(map_only_ids)].copy().drop(columns=['MODALITYID_Clean'])

# 4. 保存
df_intersection.to_excel(out_intersection, index=False)
df_phys_only.to_excel(out_physical_only, index=False)
df_map_only.to_excel(out_mapping_only, index=False)

print(f"💾 三张审计结果表已生成并存入 {temp_dir} 目录 (前缀 37_)。\n")