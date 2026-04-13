import os
import pandas as pd
import numpy as np

# ================= 配置路径 =================
temp_dir = '../Temp_data'
# 使用 37 号生成的交集映射表作为基础名单
mapping_file = os.path.join(temp_dir, '37_Intersection_Image_Mapping.xlsx')
# 最终输出给医生的标注模板
output_file = os.path.join(temp_dir, '40_Fracture_Grading_Annotation_Template.xlsx')

print("🚀 [40号] 启动骨折分级标注模板生成引擎 (极简实战版)...\n")

# ================= 1. 加载映射底座 =================
print("📂 正在加载患者影像映射基础数据...")
df_mapping = pd.read_excel(mapping_file)
# 格式标准化
df_mapping['MODALITYID'] = df_mapping['MODALITYID'].astype(str).str.strip()
df_mapping['病历号'] = df_mapping['病历号'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# ================= 2. 提取三大模态的成员名单 =================
def get_modality_set(clean_file, unmatched_file, m_type):
    path = os.path.join(temp_dir, clean_file)
    unmatch_path = os.path.join(temp_dir, unmatched_file)
    if not os.path.exists(path): return set()
    
    df = pd.read_csv(path, dtype=str)
    if os.path.exists(unmatch_path):
        df_un = pd.read_csv(unmatch_path, dtype=str)
        bad_ids = set(df_un['Image_Data_ID'].dropna().str.strip())
        df = df[~df['Image_Data_ID'].str.strip().isin(bad_ids)]
    
    mod_col = [col for col in df.columns if '(0008,0060)' in col.replace(' ', '') or 'Modality' in col][0]
    
    if m_type == 'CT': mask = df[mod_col].str.strip().str.upper() == 'CT'
    elif m_type == 'MR': mask = df[mod_col].str.strip().str.upper() == 'MR'
    else: mask = df[mod_col].str.strip().str.upper().isin(['DX', 'CR'])
    
    return set(df[mask]['Image_Data_ID'].dropna().str.strip())

print("🔍 正在扫描各模态有效影像 ID...")
ct_ids = get_modality_set('10_CT_Metadata_Clean.csv', '22_New_Unmatched_CT_Metadata_Full.csv', 'CT')
mr_ids = get_modality_set('10_MR_Metadata_Clean.csv', '22_New_Unmatched_MR_Metadata_Full.csv', 'MR')
xray_ids = get_modality_set('10_XRay_Metadata_Clean.csv', '22_New_Unmatched_XRay_Metadata_Full.csv', 'XRay')

# ================= 3. 执行全模态聚合 =================
print("🔄 正在为患者构建全模态映射矩阵...")

def check_type(m_id):
    if m_id in ct_ids: return 'CT'
    if m_id in mr_ids: return 'MR'
    if m_id in xray_ids: return 'XRay'
    return 'Other'

df_mapping['Type'] = df_mapping['MODALITYID'].apply(check_type)
# 仅保留三大核心模态
df_core = df_mapping[df_mapping['Type'] != 'Other'].copy()

# 按患者和模态类型聚合，多个文件夹ID用逗号隔开
df_pivot = df_core.groupby(['病历号', 'Type'])['MODALITYID'].apply(lambda x: ', '.join(x)).unstack(fill_value='')

# 确保三列齐全，哪怕有的模态全院都没有人做
for c in ['CT', 'MR', 'XRay']:
    if c not in df_pivot.columns: df_pivot[c] = ''

# 重置索引，让“病历号”变回一列
df_pivot = df_pivot.reset_index()

# ================= 4. 创建极简标注字段与排版 =================
print("📝 正在注入极简标注列...")

# 直接新增一列干净的“标注”
df_pivot['标注'] = ""

# 调整列顺序，确保符合你的直觉排版
df_pivot = df_pivot[['病历号', 'CT', 'MR', 'XRay', '标注']]

# 对患者 ID 进行排序
df_pivot = df_pivot.sort_values(by='病历号')

# ================= 5. 导出 Excel =================
print(f"💾 正在导出标注模板，共计 {len(df_pivot):,} 名待标注患者...")
df_pivot.to_excel(output_file, index=False)

print(f"\n🎉 完美！极简版标注模板已生成：{output_file}")