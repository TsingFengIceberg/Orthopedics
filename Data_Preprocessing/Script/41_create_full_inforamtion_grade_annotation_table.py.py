import os
import pandas as pd
import numpy as np

# ================= 配置路径 =================
temp_dir = '../Temp_data'
raw_tables_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'

mapping_file = os.path.join(temp_dir, '37_Intersection_Image_Mapping.xlsx')
clinical_file = os.path.join(raw_tables_dir, 'Comprehensive_Clinical_Records.xlsx')
output_file = os.path.join(temp_dir, '41_Final_Timeline_Annotation_Template.xlsx')

print("🚀 [44号] 启动终极全景时间轴引擎 (全局首诊时序版)...\n")

# ================= 1. 处理影像数据 =================
print("📂 正在解析影像数据...")
df_img = pd.read_excel(mapping_file)

# 格式清洗
for col in ['病历号', 'MODALITYID', '检查时间', '检查项目', 'STUDYRESULT', 'DIAGRESULT']:
    if col in df_img.columns:
        df_img[col] = df_img[col].astype(str).str.strip().replace('nan', '无记录')
df_img['病历号'] = df_img['病历号'].str.replace(r'\.0$', '', regex=True)

# 确定模态类型 (复用之前的快速扫描逻辑)
def get_modality_set(clean_file, m_type):
    path = os.path.join(temp_dir, clean_file)
    if not os.path.exists(path): return set()
    df = pd.read_csv(path, dtype=str)
    mod_col = [col for col in df.columns if '(0008,0060)' in col.replace(' ', '') or 'Modality' in col][0]
    if m_type == 'CT': mask = df[mod_col].str.strip().str.upper() == 'CT'
    elif m_type == 'MR': mask = df[mod_col].str.strip().str.upper() == 'MR'
    else: mask = df[mod_col].str.strip().str.upper().isin(['DX', 'CR'])
    return set(df[mask]['Image_Data_ID'].dropna().str.strip())

ct_ids = get_modality_set('10_CT_Metadata_Clean.csv', 'CT')
mr_ids = get_modality_set('10_MR_Metadata_Clean.csv', 'MR')
xray_ids = get_modality_set('10_XRay_Metadata_Clean.csv', 'XRay')

df_img['Type'] = df_img['MODALITYID'].apply(lambda x: 'CT' if x in ct_ids else ('MR' if x in mr_ids else ('XRay' if x in xray_ids else 'Other')))
df_core_img = df_img[df_img['Type'] != 'Other'].copy()

# 1.1 构建左侧影像列 (强制按图片时间排序)
df_core_img['排序辅助时间'] = pd.to_datetime(df_core_img['检查时间'], errors='coerce')
df_core_img = df_core_img.sort_values(by=['病历号', 'Type', '排序辅助时间'], na_position='last')

df_core_img['显示标签'] = "[" + df_core_img['检查时间'].str[:10] + "] " + df_core_img['MODALITYID']
df_img_pivot = df_core_img.groupby(['病历号', 'Type'])['显示标签'].apply(lambda x: '\n'.join(x.dropna().astype(str))).unstack(fill_value='').reset_index()

for c in ['CT', 'MR', 'XRay']:
    if c not in df_img_pivot.columns: df_img_pivot[c] = ''

# 1.2 构建影像事件流
df_img_events = pd.DataFrame({
    '病历号': df_core_img['病历号'],
    '事件时间': df_core_img['排序辅助时间'],
    '事件文本': "📸 [影像] " + df_core_img['检查时间'] + " | " + df_core_img['Type'] + " (" + df_core_img['MODALITYID'] + ")\n" +
                "   ▪ 项目: " + df_core_img['检查项目'] + "\n" +
                "   ▪ 结论: " + df_core_img['DIAGRESULT'] + "\n"
})

# ================= 2. 处理临床数据 =================
print("📂 正在解析临床数据...")
df_cli = pd.read_excel(clinical_file)
patient_col = '患者ID'  

for col in [patient_col, '住院次数', '入院时间', '出院时间', '诊断名称', '手术']:
    if col in df_cli.columns:
        df_cli[col] = df_cli[col].astype(str).str.strip().replace('nan', '无记录')
df_cli[patient_col] = df_cli[patient_col].str.replace(r'\.0$', '', regex=True)

# 构建临床事件流
df_cli_events = pd.DataFrame({
    '病历号': df_cli[patient_col],
    '事件时间': pd.to_datetime(df_cli['入院时间'], errors='coerce'),
    '事件文本': "🏥 [临床] 第" + df_cli['住院次数'] + "次住院 (入院: " + df_cli['入院时间'] + " -> 出院: " + df_cli['出院时间'] + ")\n" +
                "   ▪ 诊断: " + df_cli['诊断名称'] + "\n" +
                "   🔪 手术: " + df_cli['手术'] + "\n"
})

# ================= 3. 万物归一与全局排序 =================
print("🔄 正在执行跨模态时间轴交织与【全局首诊时间】重排...")

df_all_events = pd.concat([df_img_events, df_cli_events], ignore_index=True).dropna(subset=['病历号'])

# 🌟 关键创新点：计算每个病人的“生命周期起始点”
# 找到每个病历号对应的最小事件时间
df_first_visit = df_all_events.groupby('病历号')['事件时间'].min().reset_index()
df_first_visit.rename(columns={'事件时间': '首诊时间_排序用'}, inplace=True)

# 聚合时间轴文本 (组内按时间升序)
df_all_events = df_all_events.sort_values(by=['病历号', '事件时间'], na_position='last')
df_timeline = df_all_events.groupby('病历号')['事件文本'].apply(lambda x: '\n'.join(x.dropna().astype(str))).reset_index()
df_timeline.rename(columns={'事件文本': '全景时间轴 (临床+影像)'}, inplace=True)

# ================= 4. 组装并按照首诊时间进行【整行排序】 =================
print("🔗 正在生成最终的超级标注模板...")

df_final = pd.merge(df_img_pivot, df_timeline, on='病历号', how='left')
# 挂载首诊时间用于排序
df_final = pd.merge(df_final, df_first_visit, on='病历号', how='left')

# 核心：整行按时间顺序排列
df_final = df_final.sort_values(by='首诊时间_排序用', ascending=True, na_position='last')

# 补充标注列并清理
df_final['标注'] = ""
cols = ['病历号', 'CT', 'MR', 'XRay', '全景时间轴 (临床+影像)', '标注']
df_final = df_final[cols]

# ================= 5. 带引擎的 Excel 自动化排版 =================
print(f"💾 正在导出【打开即看版】Excel，共计 {len(df_final):,} 名患者...")

writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
df_final.to_excel(writer, index=False, sheet_name='全景标注表')

workbook  = writer.book
worksheet = writer.sheets['全景标注表']
wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})

# 设置最舒适的列宽
worksheet.set_column(0, 0, 15, wrap_format)  # 病历号
worksheet.set_column(1, 3, 30, wrap_format)  # CT/MR/XRay
worksheet.set_column(4, 4, 80, wrap_format)  # 全景时间轴
worksheet.set_column(5, 5, 20, wrap_format)  # 标注列

# 表头美化
header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'valign': 'vcenter', 'align': 'center'})
for col_num, value in enumerate(df_final.columns.values):
    worksheet.write(0, col_num, value, header_format)

writer.close()
print(f"\n🎉 完美收官！全局时序对齐的模板已生成：{output_file}")