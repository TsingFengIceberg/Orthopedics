import os
import pandas as pd
import re

# ================= 配置路径 =================
temp_dir = '../Temp_data' 
input_file = os.path.join(temp_dir, '26_Lab_Items_Full_Dictionary.csv')
output_file = os.path.join(temp_dir, '27_Lab_Items_Mapping_Draft.csv')

print("🚀 开始构建第一版【检验指标名称映射字典】...\n")

# 1. 读取我们刚生成的全量字典
df = pd.read_csv(input_file)

# 2. 提取最核心的“分析明细”
def extract_analyte(full_name):
    parts = str(full_name).split(' - ')
    if len(parts) >= 2:
        return ' - '.join(parts[1:]).strip()
    return str(full_name).strip()

df['原始明细'] = df['完整检验项 (项目 - 明细)'].apply(extract_analyte)

# 3. 第一次折叠：合并不同套餐中的同名指标
# （例如：把各个套餐里的“血红蛋白”合并在一起）
raw_analyte_counts = df.groupby('原始明细')['出现总频次'].sum().reset_index()

# 4. 生成【推荐标准名称】
def propose_standard_name(name):
    name = str(name).strip()
    # 规则A：剔除末尾可能带有的乱码字符如 * - _
    name = name.strip(' *-_')
    # 规则B：剔除中文和英文括号及其内部的内容 (用于合并 CLIA、ELISA 等方法学差异)
    name = re.sub(r'\(.*?\)|（.*?）', '', name).strip()
    return name

raw_analyte_counts['推荐标准名称'] = raw_analyte_counts['原始明细'].apply(propose_standard_name)

# 5. 第二次折叠：基于【推荐标准名称】进行变体归类统计
mapping_data = []

for std_name, group in raw_analyte_counts.groupby('推荐标准名称'):
    total_freq = group['出现总频次'].sum()
    
    # 将包含的具体变体和各自的频次拼成直观的字符串
    # 格式如： 乙型肝炎病毒表面抗原(100次) | 乙型肝炎病毒表面抗原(CLIA)(50次)
    details = []
    # 按频次从高到低排序一下变体，方便查看
    group_sorted = group.sort_values(by='出现总频次', ascending=False)
    for _, row in group_sorted.iterrows():
        details.append(f"{row['原始明细']} (频次:{row['出现总频次']})")
        
    mapping_data.append({
        '推荐标准名称': std_name,
        '总合并频次': total_freq,
        '合并项数量': len(group),
        '包含的原始明细变体': '  |  '.join(details)
    })

# 6. 生成最终的映射字典 DataFrame
mapping_df = pd.DataFrame(mapping_data)

# 7. 排序：先把有合并动作的（合并项数量>1）排在前面，频次高的排在前面
mapping_df.sort_values(by=['合并项数量', '总合并频次'], ascending=[False, False], inplace=True)

# 8. 导出为 CSV
mapping_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"✅ 第一版映射字典已生成！共产生了 {len(mapping_df)} 个独立标准名称。")
print(f"💾 请打开 {output_file} 进行人工审阅。")

# 预览一下发生了合并的 Top 5 数据
print("\n👀 预览：发现疑似变体并建议合并的 Top 5 案例：")
merged_preview = mapping_df[mapping_df['合并项数量'] > 1].head(5)
for _, row in merged_preview.iterrows():
    print(f"\n🔹 【推荐标准名称】: {row['推荐标准名称']}  (总频次: {row['总合并频次']})")
    print(f"   ┣ 包含变体: {row['包含的原始明细变体']}")

print("\n💡 下一步行动指南：")
print("打开导出的 CSV，如果有误杀（比如把 CV 和 SD 错合并了），直接在表里把它们拆开修改即可！我们最终的合并将绝对服从你修改后的这张字典表。")