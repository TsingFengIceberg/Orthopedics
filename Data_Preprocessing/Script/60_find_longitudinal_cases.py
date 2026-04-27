import pandas as pd
import re
import os

# ==========================================
# 🌟 60号脚本：纵向多期 CT 黄金病例挖掘器 (带高级排版)
# ==========================================

def extract_longitudinal_cases():
    # 路径配置
    base_dir = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'
    input_path = os.path.join(base_dir, '42_Flexible_Row_Annotation_Template.xlsx')
    output_path = os.path.join(base_dir, '60_Multiple_Admissions_CT_Cases.xlsx')
    
    print("🔍 正在加载原始标注表...")
    try:
        df = pd.read_excel(input_path)
    except FileNotFoundError:
        print(f"❌ 找不到文件: {input_path}")
        return

    valid_patient_ids = []
    
    # 按照病历号进行分组
    grouped = df.groupby('病历号')
    
    print(f"⏱️ 开始遍历 {len(grouped)} 位患者的纵向病史...")
    for pid, group in grouped:
        # 1. 寻找该病人的首行（临床病史汇总）
        summary_row = group[group['记录类型'] == '🏥 临床病史汇总']
        if summary_row.empty:
            continue
            
        summary_text = str(summary_row.iloc[0]['内容详情'])
        
        # 2. 正则表达式匹配“第X次住院”
        admissions = re.findall(r'第\d+次住院', summary_text)
        
        # 条件A：至少有2次住院记录
        if len(admissions) < 2:
            continue
            
        # 3. 检查该病人的 CT 影像记录
        ct_rows = group[group['影像模态'] == 'CT']
        
        # 条件B：至少有2次【不同时间】的 CT 影像
        unique_ct_times = ct_rows['发生时间'].nunique()
        
        if unique_ct_times >= 2:
            valid_patient_ids.append(pid)
            
    # 提取符合条件的病人全量行
    final_df = df[df['病历号'].isin(valid_patient_ids)]
    
    if final_df.empty:
        print("⚠️ 未找到符合条件的病例。")
        return

    # ================= 自动化高级排版导出 =================
    print(f"💾 正在导出【带高级排版】的筛选结果，总计行数 {len(final_df):,} 行...")

    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
    sheet_name = '黄金病例筛选表'
    final_df.to_excel(writer, index=False, sheet_name=sheet_name)

    workbook  = writer.book
    worksheet = writer.sheets[sheet_name]
    wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    border_wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})

    # 1. 设定各列的最佳阅读宽度 (与42号完全一致)
    worksheet.set_column(0, 0, 15, wrap_format)  # A: 病历号
    worksheet.set_column(1, 1, 16, wrap_format)  # B: 记录类型
    worksheet.set_column(2, 2, 12, wrap_format)  # C: 发生时间
    worksheet.set_column(3, 3, 10, wrap_format)  # D: 影像模态
    worksheet.set_column(4, 4, 15, wrap_format)  # E: 文件夹ID
    worksheet.set_column(5, 5, 80, wrap_format)  # F: 内容详情
    worksheet.set_column(6, 6, 20, border_wrap_format)  # G: 医生独立标注

    # 2. 🌟 魔法高亮特效：将“临床病史汇总”所在行标为淡蓝色
    highlight_format = workbook.add_format({'bg_color': '#DDEBF7', 'bold': True})
    worksheet.conditional_format(f'A2:G{len(final_df)+1}', {
        'type': 'formula',
        'criteria': '=$B2="🏥 临床病史汇总"',
        'format': highlight_format
    })

    # 3. 固化表头
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    for col_num, value in enumerate(final_df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # 冻结第一行表头
    worksheet.freeze_panes(1, 0)

    writer.close()
    
    print("\n==========================================")
    print(f"🎯 挖掘完成！")
    print(f"   👤 符合条件的黄金患者数: {len(valid_patient_ids)} 人")
    print(f"💾 排版结果已保存至: {output_path}")
    print("==========================================")

if __name__ == '__main__':
    extract_longitudinal_cases()