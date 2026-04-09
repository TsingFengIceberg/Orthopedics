import os
import pandas as pd

# ================= 配置路径 =================
data_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'
final_map_file = '../Temp_data/32_Lab_Master_Mapping_Final_Grouped.xlsx'

print("🚀 启动【直击原始底表的无损覆盖校验探针】...\n")

# 1. 加载我们最终的映射字典
df_final = pd.read_excel(final_map_file)
# 去掉视觉空行
df_final = df_final.dropna(subset=['原始指标明细'])
# 提取字典中所有录入的原始名字
mapped_originals = set(df_final['原始指标明细'].astype(str).str.strip())

print(f"✅ 成功加载最终映射字典，共收录 {len(mapped_originals)} 个指标变体。")

# 2. 遍历加载三大原始底表，提取所有真实出现过的指标
lab_files = ['Lab_Results_1.xlsx', 'Lab_Results_2.xlsx', 'Lab_Results_3.xlsx']
raw_unique_items = set()
total_raw_rows = 0

print(f"\n📂 正在逐行扫描原始底表 (需要一点时间读取大表)...\n")

def clean_analyte_name(name):
    """
    完全对齐咱们之前提炼指标的脱水规则，
    确保底表取出来的名字和字典里的一模一样。
    """
    name = str(name)
    parts = name.split(' - ')
    core_name = parts[-1] if len(parts) >= 2 else name 
    return core_name.strip(' *-_')

for file in lab_files:
    file_path = os.path.join(data_dir, file)
    if not os.path.exists(file_path):
        print(f"⚠️ 找不到底表文件: {file}")
        continue
        
    print(f"读取底表 -> {file} ...")
    
    # 为了防止吃尽内存，我们只读有用的列
    # 兼容性寻找列名（你的表里可能是'分析明细'或'完整检验项 (项目 - 明细)'）
    try:
        # 先试着只读表头找出正确的列名
        preview_df = pd.read_excel(file_path, nrows=0)
        col_to_use = '分析明细' if '分析明细' in preview_df.columns else '完整检验项 (项目 - 明细)'
        
        # 正式读取那一列
        df_raw = pd.read_excel(file_path, usecols=[col_to_use])
        
        # 提取并清洗所有名称
        cleaned_names = df_raw[col_to_use].apply(clean_analyte_name)
        raw_unique_items.update(cleaned_names.unique())
        total_raw_rows += len(df_raw)
        
    except Exception as e:
        print(f"❌ 读取 {file} 出错: {e}")

print(f"\n📊 [底表核验] 扫描完毕！三大底表共计处理了 {total_raw_rows:,} 行检验记录。")
print(f"📊 [底表核验] 从千万级底表中，一共提炼出 {len(raw_unique_items)} 个绝对不重复的化验明细。")

# 3. 终极对账 (Reconciliation)
print("\n🔍 开始执行【原始底表 🆚 Final字典】绝对壁垒核验...")

missing_in_dict = raw_unique_items - mapped_originals

if len(missing_in_dict) == 0:
    print("\n✅ 终极审计：完美通过！(PASSED)")
    print("💯 结论：100% 绝对覆盖！三大原始 Excel 底表里的【每一个】化验指标，都已经安全着陆在我们的 Final 字典里了。没有一条数据成为孤儿！")
else:
    print("\n❌ 终极审计：警报！发现底表存在漏网之鱼！(FAILED)")
    print(f"⚠️ 警告：有 {len(missing_in_dict)} 个指标真实存在于原始底表，但咱们的字典居然没收录它！它们是：")
    for item in missing_in_dict:
        print(f"  - {item}")
        
    print("\n💡 建议行动：如果上面有字，请立即把这些漏掉的名字补进咱们的脚本映射规则里！")