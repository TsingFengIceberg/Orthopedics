import os
import pandas as pd

# ================= 配置路径 =================
temp_dir = '../Temp_data' 
input_file = os.path.join(temp_dir, '26_Lab_Items_Full_Dictionary.csv')
output_file = os.path.join(temp_dir, '28_Lab_Items_Mapping_Draft.csv')

print("🚀 基于医学规则，开始构建第二版【安全验证版】映射字典...\n")

# ================= 核心白名单：安全合并映射字典 =================
# 只有在这个字典左边的词，才会被强行转换为右边的标准词
SAFE_MERGE_DICT = {
    # 1. 传染病与抗原抗体（消除方法学和中英文缩写差异）
    '乙型肝炎病毒表面抗原(CLIA)': '乙型肝炎病毒表面抗原',
    '乙型肝炎病毒表面抗原(ELISA)': '乙型肝炎病毒表面抗原',
    '丙型肝炎病毒抗体(CLIA)': '丙型肝炎病毒抗体',
    '丙型肝炎病毒抗体(ELISA)': '丙型肝炎病毒抗体',
    '梅毒特异性抗体(TP-ELISA)': '梅毒特异性抗体',
    '梅毒特异性抗体(CLIA)': '梅毒特异性抗体',
    '梅毒特异性抗体(TPPA)': '梅毒特异性抗体',
    '人类免疫缺陷病毒抗原抗体(CLIA)': '人类免疫缺陷病毒抗原抗体',
    '人免疫缺陷病毒抗原抗体(ELISA)': '人类免疫缺陷病毒抗原抗体',
    '人免疫缺陷病毒抗原抗体(CLIA)': '人类免疫缺陷病毒抗原抗体',
    '乙型肝炎病毒e抗体(ELISA)': '乙型肝炎病毒e抗体',
    '乙型肝炎病毒e抗体(CLIA)': '乙型肝炎病毒e抗体',
    '乙型肝炎病毒e抗原(ELISA)': '乙型肝炎病毒e抗原',
    '乙型肝炎病毒e抗原(CLIA)': '乙型肝炎病毒e抗原',
    '乙型肝炎病毒核心抗体(ELISA)': '乙型肝炎病毒核心抗体',
    '乙型肝炎病毒核心抗体(CLIA)': '乙型肝炎病毒核心抗体',
    '乙型肝炎病毒表面抗体(ELISA)': '乙型肝炎病毒表面抗体',
    '乙型肝炎病毒表面抗体(CLIA)': '乙型肝炎病毒表面抗体',
    '乙型肝炎病毒核心抗体IgM(ELISA)': '乙型肝炎病毒核心抗体IgM',
    '乙型肝炎病毒核心抗体IgM(CLIA)': '乙型肝炎病毒核心抗体IgM',
    
    # 2. 肿瘤标志物与生化（去除英文尾缀）
    '总前列腺特异性抗原(tPSA)': '总前列腺特异性抗原',
    '总前列腺特异性抗原（tPSA）': '总前列腺特异性抗原',
    '游离前列腺特异性抗原(fPSA)': '游离前列腺特异性抗原',
    '游离前列腺特异性抗原（fPSA）': '游离前列腺特异性抗原',
    '胃蛋白酶原Ⅰ(PGⅠ)': '胃蛋白酶原Ⅰ',
    '胃蛋白酶原Ⅱ(PGⅡ)': '胃蛋白酶原Ⅱ',
    
    # 3. 骨代谢关键指标
    '总Ⅰ型(前)胶原氨基端延长肽': '总Ⅰ型胶原氨基端延长肽',
    
    # 4. 常规检验同义词统一定义
    '血沉（毛细管法）': '血沉',
    '血沉（光度计法）': '血沉',
    '国际标准化比率': '国际标准化比值',
    '血小板数': '血小板计数',
    'UN:CREA': 'BUN:CREA',
    
    # 5. 错别字/标点/异体字无损修复
    'a-L-岩藻糖甘酶': 'a-L-岩藻糖苷酶',
    '病理性管型': '病理管型',
    '酵母样菌': '酵母菌',
    '胃泌素释放前肽前体': '胃泌素释放肽前体',
    '谷氨酰转酞酶': '谷氨酰转肽酶',
    '谷氨酰基转肽酶': '谷氨酰转肽酶',
    '亮氨酸氨基转肽酶': '亮氨酸氨基肽酶',
    '腺苷酸脱氨酶': '腺苷脱氨酶',
    '超敏C-反应蛋白': '超敏C反应蛋白',
    '糖类抗原153': '糖类抗原15-3',
    '糖类抗原199': '糖类抗原19-9'
}

# 1. 读取字典
df = pd.read_csv(input_file)

# 2. 提取核心分析明细
def extract_analyte(full_name):
    parts = str(full_name).split(' - ')
    if len(parts) >= 2:
        return ' - '.join(parts[1:]).strip()
    return str(full_name).strip()

df['原始明细'] = df['完整检验项 (项目 - 明细)'].apply(extract_analyte)

# 去除首尾脏字符，但不做任何内部替换
df['原始明细'] = df['原始明细'].str.strip(' *-_')

# 第一次折叠：合并跨套餐的同名指标
raw_analyte_counts = df.groupby('原始明细')['出现总频次'].sum().reset_index()

# 3. 执行安全的字典映射
def safe_map(name):
    # 如果在安全白名单里，就替换；如果不在，原封不动返回
    return SAFE_MERGE_DICT.get(name, name)

raw_analyte_counts['推荐标准名称'] = raw_analyte_counts['原始明细'].apply(safe_map)

# 4. 第二次折叠：生成最终合并表
mapping_data = []

for std_name, group in raw_analyte_counts.groupby('推荐标准名称'):
    total_freq = group['出现总频次'].sum()
    
    details = []
    group_sorted = group.sort_values(by='出现总频次', ascending=False)
    for _, row in group_sorted.iterrows():
        details.append(f"{row['原始明细']} (频次:{row['出现总频次']})")
        
    mapping_data.append({
        '推荐标准名称': std_name,
        '总合并频次': total_freq,
        '合并项数量': len(group),
        '包含的原始明细变体': '  |  '.join(details)
    })

# 5. 生成 DataFrame 并导出
mapping_df = pd.DataFrame(mapping_data)
mapping_df.sort_values(by=['合并项数量', '总合并频次'], ascending=[False, False], inplace=True)
mapping_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"✅ 第二版安全映射字典已生成！文件保存至: {output_file}")
print("💡 这一版完美避开了(CV)/(SD)、(镜检)的误杀陷阱，留给医生审阅的将是一份精确严谨的名单。")