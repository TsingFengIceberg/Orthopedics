import os
import pandas as pd
import itertools

# ================= 配置路径 =================
raw_tables_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'
temp_dir = '../Temp_data'

files = {
    '1. 影像映射表 (交集后)': {'path': os.path.join(temp_dir, '37_Intersection_Image_Mapping.xlsx'), 'id_col': '病历号'},
    '2. 综合临床记录': {'path': os.path.join(raw_tables_dir, 'Comprehensive_Clinical_Records.xlsx'), 'id_col': '患者ID'},
    '3. 护理评估': {'path': os.path.join(raw_tables_dir, 'Nursing_Assessments.xlsx'), 'id_col': 'PATIENT_ID'},
    '4. 疼痛评分': {'path': os.path.join(raw_tables_dir, 'Pain_Scores.xlsx'), 'id_col': 'PATIENT_ID'},
    '5. 化验大宽表': {'path': os.path.join(temp_dir, '35_Lab_Wide_Table.csv'), 'id_col': '患者编号'}
}

out_all_5_file = os.path.join(temp_dir, '38_Intersection_All_5_Patient_IDs.xlsx')

print("🚀 [38号] 启动五维多模态患者交集分析引擎...\n")

def clean_patient_id(series):
    """
    终极 ID 洗套器：
    防止 Excel 把纯数字 ID (如 12345) 读成浮点数 (12345.0)，导致集合匹配失败。
    """
    return series.dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# 1. 提取五大维度的独立患者集合
patient_sets = {}

for name, info in files.items():
    print(f"📂 正在加载 [{name}] ...")
    if info['path'].endswith('.csv'):
        df = pd.read_csv(info['path'], usecols=[info['id_col']])
    else:
        df = pd.read_excel(info['path'], usecols=[info['id_col']])
        
    ids = set(clean_patient_id(df[info['id_col']]))
    patient_sets[name] = ids
    print(f"   -> 发现独立患者：{len(ids):,} 人")

print("\n" + "="*50)
print("📊 [多模态患者交集统计矩阵]")
print("="*50)

# 2. 动态计算所有的组合交集 (2个, 3个, 4个, 5个)
set_names = list(patient_sets.keys())

for r in range(2, 6): # r 代表组合的数量 (2 到 5)
    print(f"\n【 {r} 张表共同存在的患者交集 】")
    combinations = list(itertools.combinations(set_names, r))
    
    for combo in combinations:
        # 获取第一个集合作为基底
        intersection_result = patient_sets[combo[0]]
        # 依次与其他集合求交集
        for other_set_name in combo[1:]:
            intersection_result = intersection_result.intersection(patient_sets[other_set_name])
        
        # 简化名字输出，让终端看着不那么乱
        short_names = [n.split('.')[0].strip() for n in combo]
        print(f"  ♦ {' + '.join(short_names)}: {len(intersection_result):,} 人")
        
        # 3. 如果是 5 张表的终极交集，保存下来
        if r == 5:
            ultimate_intersection = intersection_result

# 4. 保存终极 5 维护照
print("\n" + "="*50)
df_ultimate = pd.DataFrame({'五表全通患者ID': list(ultimate_intersection)})
df_ultimate.to_excel(out_all_5_file, index=False)
print(f"🎉 大满贯！五大维度全覆盖的“多模态黄金患者”共计 {len(ultimate_intersection):,} 人。")
print(f"💾 这批患者的 ID 名单已安全隔离至: {out_all_5_file}")