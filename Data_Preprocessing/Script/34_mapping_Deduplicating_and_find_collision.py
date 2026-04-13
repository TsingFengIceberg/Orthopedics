'''
### 🛡️ 四大核心筛选法则（深度解析）

任何一条原始数据，想要活到最后那张 `34_Mapped_Cleaned` 干净表里，必须经历以下四重极其严苛的考验：

#### 第一关：格式防杠法则（`safe_float` 转换）
* **它在干什么**：系统导出的数据里，同一个数值 4，可能被存成了文本 `"4"`、文本 `"4.0"` 或者纯数字 `4`。这会让机器误以为它们是不同的结果。这关强制把它们统一剥掉外衣，洗成标准的浮点数。
* **效果**：消灭了由于“数据类型和零的个数”不同而引发的假冲突。

#### 第二关：绝对复印件清理法则（漏斗 1）
* **判定主键**：`[患者、时间、项目名称(大项)、分析明细(最原始的小项名字)、对齐后的结果]`。
* **它在干什么**：如果两行数据在这 5 个维度上**连一根头发丝的区别都没有**，那说明这纯粹是 LIS 系统卡顿重发，或者数据库 Join 错误导致的数据翻倍。
* **执行动作**：无脑去重（`drop_duplicates`），只留 1 条。即使是没有时间（NaN）的数据，只要其他几项完全一致，也会被当做同一条处理。

#### 第三关：等值伪碰撞拯救法则（漏斗 2）
* **判定主键**：`[患者、时间、项目名称(大项)、标准检验项名称(映射后的小项名字)、对齐后的结果]`。
* **它在干什么**：这是为了拯救你的同义词！假设张三在同一次“急诊生化”套餐里，系统既报了一个 `葡萄糖(空腹)` 是 5.8，又报了一个 `快速血糖` 是 5.8。经过我们的字典映射后，它们都变成了标准名 `葡萄糖`。此时，它们的大项相同、小项相同、结果也相同。
* **执行动作**：因为结果不矛盾，代码会聪明地把它们**合并保留为 1 条**。这避免了同义词因为抢地盘而被误杀。

#### 第四关：致命矛盾绝杀法则（漏斗 3）
* **判定主键**：`[患者、时间、项目名称(大项)、标准检验项名称(映射后的小项名字)]`。
* **它在干什么**：这是最后一道死亡防线。如果两行数据闯过了前三关，来到了这里，说明它们的**化验结果必定是不同的**！（如果是相同的，早就被漏斗 2 合并了）。
  * 比如：同人、同时间、同在“急诊生化”里，但一个名叫 `白细胞` 的值是 4.5，另一个名叫 `白细胞数` 的值是 18.0。映射后它们都叫 `白细胞`，发生了抢同一个格子的流血冲突。
* **执行动作**：触发最高警报（`keep=False`）。不猜谁真谁假，**连坐机制，全部硬剔除（Hard Trim）**，一起关进 `34_Collision_Audit_Log` 审计表，绝不让脏数据流出。

这四道关卡环环相扣，既兼顾了数据的“最大保留率”，又守住了“绝不引入矛盾特征”的死基线。带着这段代码，你就可以非常踏实地迈向下一步的大宽表转置了！
'''


import os
import pandas as pd
import numpy as np

# ================= 配置路径 =================
data_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'
temp_dir = '../Temp_data'
mapping_file = os.path.join(temp_dir, '32_Lab_Master_Mapping_Final_Grouped.xlsx')
collision_log_file = os.path.join(temp_dir, '34_Collision_Audit_Log.xlsx')

print("🚀 启动【极高精度检验映射与同源防撞隔离引擎】(大项联合防撞终极版)...\n")

# ================= 1. 加载映射字典 =================
df_map = pd.read_excel(mapping_file)
df_map = df_map.dropna(subset=['原始指标明细', '合并后标准名称'])

# 构建哈希查询字典: { '白细胞数': '白细胞', '红细胞(镜检)': '镜检红细胞', ... }
mapping_dict = dict(zip(df_map['原始指标明细'].astype(str).str.strip(), 
                        df_map['合并后标准名称'].astype(str).str.strip()))

print(f"✅ 成功加载字典，共就绪 {len(mapping_dict)} 条映射规则。")

# ================= 2. 读取并合并三张原始长表 =================
lab_files = ['Lab_Results_1.xlsx', 'Lab_Results_2.xlsx', 'Lab_Results_3.xlsx']
all_dfs = []

print("📂 正在加载并合并三大原始检验表...")
for file in lab_files:
    file_path = os.path.join(data_dir, file)
    if not os.path.exists(file_path): continue
    
    df = pd.read_excel(file_path)
    # 处理开头无名字的顺序标号列 (如 Unnamed: 0)，防止其干扰去重
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['Source_File'] = file 
    all_dfs.append(df)

big_df = pd.concat(all_dfs, ignore_index=True)
initial_rows = len(big_df)
print(f"📊 共加载原始长表数据：{initial_rows:,} 行。")

# ================= 3. 数值格式化洗套 (0 vs 0.0) =================
print("🧹 正在执行数值格式化洗套...")

def safe_float(val):
    if pd.isna(val): return val
    try:
        return float(val)
    except (ValueError, TypeError):
        return str(val).strip()

big_df['对齐后结果'] = big_df['结果'].apply(safe_float)

# ================= 4. 执行全面名称映射 =================
print("🔄 正在执行全量指标名称标准化映射...")

def extract_analyte(name):
    name = str(name)
    parts = name.split(' - ')
    return parts[-1].strip(' *-_') if len(parts) >= 2 else name.strip(' *-_')

big_df['原始脱水名称'] = big_df['分析明细'].apply(extract_analyte)
big_df['标准检验项名称'] = big_df['原始脱水名称'].apply(lambda x: mapping_dict.get(x, x))


# ================= 5. 高阶防撞多重漏斗 (⚠️ 核心逻辑区) =================

# --- 漏斗 1：消除纯系统级绝对重复 (场景 A) ---
big_df = big_df.drop_duplicates(subset=['患者编号', '报告时间', '项目名称', '分析明细', '对齐后结果'])
dedup_rows_1 = initial_rows - len(big_df)
print(f"🧹 漏斗 1 (系统冗余清理)：剔除 {dedup_rows_1:,} 行绝对重复数据。")

# --- 漏斗 2：拯救“等值伪碰撞” (场景 B) ---
before_funnel_2 = len(big_df)
big_df = big_df.drop_duplicates(subset=['患者编号', '报告时间', '项目名称', '标准检验项名称', '对齐后结果'])
saved_pseudo_collisions = before_funnel_2 - len(big_df)
print(f"🛡️ 漏斗 2 (等值伪碰撞拯救)：成功拯救并合并了 {saved_pseudo_collisions:,} 行等值冲突数据。")

# --- 漏斗 3：揪出真正的致命矛盾并执行硬剔除 (场景 C) ---
print("🚨 正在执行漏斗 3：排查绝对矛盾碰撞...")
conflict_keys = ['患者编号', '报告时间', '项目名称', '标准检验项名称']

# keep=False：互相引爆，全部踢走
is_true_conflict = big_df.duplicated(subset=conflict_keys, keep=False)

collision_df = big_df[is_true_conflict].copy()
clean_df = big_df[~is_true_conflict].copy()

conflict_count = len(collision_df)
print(f"💥 漏斗 3 (致命矛盾剔除)：发现并剔除了 {conflict_count:,} 行数值矛盾撞车数据！")

# ================= 6. 分装输出至 Temp_data =================
print("\n💾 正在保存极净映射长表与审计日志...")

if conflict_count > 0:
    collision_df = collision_df.sort_values(by=['患者编号', '报告时间', '项目名称', '标准检验项名称'])
    collision_df.drop(columns=['Source_File', '原始脱水名称', '对齐后结果']).to_excel(collision_log_file, index=False)
    print(f"   [审计留存] 致命矛盾明细已安全隔离至: {collision_log_file}")

for file in lab_files:
    sub_clean_df = clean_df[clean_df['Source_File'] == file].copy()
    
    # 覆盖老旧结果，保证输出纯净
    sub_clean_df['结果'] = sub_clean_df['对齐后结果']
    sub_clean_df = sub_clean_df.drop(columns=['Source_File', '原始脱水名称', '对齐后结果'])
    
    out_path = os.path.join(temp_dir, f"34_Mapped_Cleaned_{file}")
    sub_clean_df.to_excel(out_path, index=False)
    print(f"   [成功输出] 极净映射长表: {out_path} ({len(sub_clean_df):,} 行)")

print("\n🎉 长表逻辑与宽表逻辑已完美对齐！代码重构完毕！")