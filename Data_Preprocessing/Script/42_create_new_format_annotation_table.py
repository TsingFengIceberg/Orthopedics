import os
import pandas as pd
import numpy as np

# ================= 配置路径 =================
temp_dir = '../Temp_data'
raw_tables_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'

mapping_file = os.path.join(temp_dir, '37_Intersection_Image_Mapping.xlsx')
clinical_file = os.path.join(raw_tables_dir, 'Comprehensive_Clinical_Records.xlsx')
output_file = os.path.join(temp_dir, '42_Flexible_Row_Annotation_Template.xlsx')

print("🚀 [42号] 启动灵活分行式全景标注模板引擎...\n")

# ================= 1. 构建影像明细行 (一行一片) =================
print("📸 正在解析影像数据，构建影像明细行...")
df_img = pd.read_excel(mapping_file)
for col in ['病历号', 'MODALITYID', '检查时间', '检查项目', 'STUDYRESULT', 'DIAGRESULT']:
    if col in df_img.columns: df_img[col] = df_img[col].astype(str).str.strip().replace('nan', '无记录')
df_img['病历号'] = df_img['病历号'].str.replace(r'\.0$', '', regex=True)

# 提取有效模态
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

# 组装影像行 DataFrame
df_img_rows = pd.DataFrame({
    '病历号': df_core_img['病历号'],
    '排版优先级': 1, # 设定为 1，排在临床后面
    '记录类型': '📸 影像单片',
    '发生时间': df_core_img['检查时间'].str[:10],
    '排序用时间': pd.to_datetime(df_core_img['检查时间'], errors='coerce'),
    '影像模态': df_core_img['Type'],
    '文件夹ID': df_core_img['MODALITYID'],
    '内容详情': "▪ 项目: " + df_core_img['检查项目'] + "\n▪ 结论: " + df_core_img['DIAGRESULT']
})

# ================= 2. 构建临床汇总行 (一患一行) =================
print("🏥 正在解析临床数据，聚合纯临床时间轴...")
df_cli = pd.read_excel(clinical_file)
patient_col = '患者ID'  
for col in [patient_col, '住院次数', '入院时间', '出院时间', '诊断名称', '手术']:
    if col in df_cli.columns: df_cli[col] = df_cli[col].astype(str).str.strip().replace('nan', '无记录')
df_cli[patient_col] = df_cli[patient_col].str.replace(r'\.0$', '', regex=True)

# 2.1 组装单条临床事件
df_cli['事件时间'] = pd.to_datetime(df_cli['入院时间'], errors='coerce')
df_cli['事件文本'] = "🏥 第" + df_cli['住院次数'] + "次住院 (入: " + df_cli['入院时间'] + " 出: " + df_cli['出院时间'] + ")\n" + \
                     "   ▪ 诊断: " + df_cli['诊断名称'] + "\n" + \
                     "   🔪 手术: " + df_cli['手术'] + "\n"

# 2.2 按病人聚合出一条完整的临床时间轴
df_cli = df_cli.sort_values(by=[patient_col, '事件时间'], na_position='first')
df_cli_timeline = df_cli.groupby(patient_col)['事件文本'].apply(lambda x: '\n'.join(x.dropna().astype(str))).reset_index()

# 2.3 组装临床行 DataFrame
df_cli_rows = pd.DataFrame({
    '病历号': df_cli_timeline[patient_col],
    '排版优先级': 0, # 设定为 0，绝对排在每个病人的第一行
    '记录类型': '🏥 临床病史汇总',
    '发生时间': '全局概览',
    '排序用时间': pd.to_datetime('1900-01-01'), # 占位符，主要靠优先级排序
    '影像模态': '—',
    '文件夹ID': '—',
    '内容详情': df_cli_timeline['事件文本']
})

# ================= 3. 上下拼接与全局排序 =================
print("🔄 正在执行行级拼接与智能排序...")
df_final = pd.concat([df_cli_rows, df_img_rows], ignore_index=True)

# 确保只保留有效病历号
df_final = df_final.dropna(subset=['病历号'])

# 核心排序逻辑：病历号聚合 -> 优先级(0比1前) -> 时间先后
df_final = df_final.sort_values(by=['病历号', '排版优先级', '排序用时间'], na_position='last')

# 丢弃辅助排序的列，加入标注列
df_final = df_final.drop(columns=['排版优先级', '排序用时间'])
df_final['医生独立标注'] = ""

# ================= 4. 自动化高级排版导出 =================
print(f"💾 正在导出【灵活分行版】Excel，总计行数 {len(df_final):,} 行...")

writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
df_final.to_excel(writer, index=False, sheet_name='分行标注表')

workbook  = writer.book
worksheet = writer.sheets['分行标注表']
wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
border_wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})

# 1. 设定各列的最佳阅读宽度
worksheet.set_column(0, 0, 15, wrap_format)  # A: 病历号
worksheet.set_column(1, 1, 16, wrap_format)  # B: 记录类型
worksheet.set_column(2, 2, 12, wrap_format)  # C: 发生时间
worksheet.set_column(3, 3, 10, wrap_format)  # D: 影像模态
worksheet.set_column(4, 4, 15, wrap_format)  # E: 文件夹ID
worksheet.set_column(5, 5, 80, wrap_format)  # F: 内容详情 (极宽，容纳临床大段文字)
worksheet.set_column(6, 6, 20, border_wrap_format)  # G: 标注列 (加个边框，提示医生在这里写字)

# 2. 🌟 魔法高亮特效：利用条件格式，将“临床病史汇总”所在行标为淡蓝色
# 这样医生在滚动时，一看到蓝色条带，就知道这是一个新病人的开始
highlight_format = workbook.add_format({'bg_color': '#DDEBF7', 'bold': True})
worksheet.conditional_format(f'A2:G{len(df_final)+1}', {
    'type': 'formula',
    'criteria': '=$B2="🏥 临床病史汇总"',
    'format': highlight_format
})

# 3. 固化表头
header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
for col_num, value in enumerate(df_final.columns.values):
    worksheet.write(0, col_num, value, header_format)

# 冻结第一行表头，医生往下滚也能看到列名
worksheet.freeze_panes(1, 0)

writer.close()
print(f"\n🎉 完美绝杀！支持医生自由框选的灵活标注模板已生成：{output_file}")