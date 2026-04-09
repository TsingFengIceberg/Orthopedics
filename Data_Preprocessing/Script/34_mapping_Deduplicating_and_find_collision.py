'''
### 📚 终极盘点：目前的完整筛选清洗规则

这段代码在底层建立了一个极其森严的**“数据清洗四步漏斗”**，任何一条长表数据想要活到最后，必须经历以下考验：

#### 第一关：格式洗套（Format Standardization）
* **规则：** 所有的化验数值，只要能被转化为浮点数（Float），统统转化。
* **效果：** 彻底粉碎因为导出格式不同导致的 `"0"` 和 `"0.0"`，`"4"` 和 `"4.0"` 的假象冲突。不能转化的（如 `阳性`、`3-5`）保留原样。

#### 第二关：系统冗余清理（System Redundancy Dedup）
* **规则：** 审查 `[患者ID + 报告时间 + 原始名称 + 结果值 + 项目名称]`。只要这 5 个完全一模一样。
* **效果：** 无论有没有时间，直接去重保留 1 条。这消灭了数据库表单联合查询（SQL Join）带来的无脑冗余拷贝。

#### 第三关：等值伪碰撞拯救（Pseudo-Collision Rescue）
* **规则：** 映射统一名称后，审查 `[患者ID + 报告时间(包含NaN) + 映射后标准名称 + 对齐后结果]`。如果这 4 个一模一样，保留 1 条。
* **效果：** 完美拯救了那些**不同套餐调用了同一管血结果**的数据（比如急诊白细胞和普通白细胞同时存在且值相等），也顺带完美合并了你关心的“没有日期但其他三项完全相同”的数据。

#### 第四关：致命矛盾绝杀（Fatal Conflict Eradication）
* **规则：** 经过前三关后，如果还存在 `[患者ID + 报告时间(包含NaN) + 映射后标准名称]` 相同的数据，此时它们的**化验结果必定不同**！
* **效果：** 触发 `keep=False` 绝杀指令！不管谁真谁假，只要发生数值矛盾，将这些涉事行**全部连根拔起**，扔进 `34_Collision_Audit_Log` 审计黑名单里，绝不允许其污染下一步的大模型特征矩阵。
'''


import os
import pandas as pd
import numpy as np

# ================= 配置路径 =================
data_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'
temp_dir = '../Temp_data'
mapping_file = os.path.join(temp_dir, '32_Lab_Master_Mapping_Final_Grouped.xlsx')
collision_log_file = os.path.join(temp_dir, '34_Collision_Audit_Log.xlsx')

print("🚀 启动【极高精度检验映射与同源防撞隔离引擎】(无时间宽容 + 等值保留版)...\n")

# ================= 1. 加载映射字典 =================
df_map = pd.read_excel(mapping_file)
df_map = df_map.dropna(subset=['原始指标明细', '合并后标准名称'])

# 构建哈希查询字典
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
print("🧹 正在执行数值格式化洗套 (统一 '0' 与 '0.0' 等数值表达)...")

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


# ================= 5. 高阶防撞多重漏斗 (核心逻辑区) =================

# --- 漏斗 1：消除纯系统级绝对重复 (场景 A) ---
# 连原始名称都一模一样的纯废数据，直接去重
big_df = big_df.drop_duplicates(subset=['患者编号', '报告时间', '分析明细', '对齐后结果', '项目名称'])
dedup_rows_1 = initial_rows - len(big_df)
print(f"🧹 漏斗 1 (系统冗余清理)：剔除 {dedup_rows_1:,} 行绝对重复数据。")

# --- 漏斗 2：拯救“等值伪碰撞” (场景 B) ---
# 映射后名称一样，数值也一样（不管有没有时间）。合并保留一条！
before_funnel_2 = len(big_df)
big_df = big_df.drop_duplicates(subset=['患者编号', '报告时间', '标准检验项名称', '对齐后结果'])
saved_pseudo_collisions = before_funnel_2 - len(big_df)
print(f"🛡️ 漏斗 2 (等值伪碰撞拯救)：成功拯救并合并了 {saved_pseudo_collisions:,} 行等值冲突数据。")

# --- 漏斗 3：揪出真正的致命矛盾并执行硬剔除 (场景 C) ---
print("🚨 正在执行漏斗 3：排查绝对矛盾碰撞 (同人、同时间、同标准名，但【数值不同】的数据)...")
conflict_keys = ['患者编号', '报告时间', '标准检验项名称']

# keep=False：只要主键相同，说明在经过漏斗2之后结果必定不同了，互相引爆全部踢走！
is_true_conflict = big_df.duplicated(subset=conflict_keys, keep=False)

collision_df = big_df[is_true_conflict].copy()
clean_df = big_df[~is_true_conflict].copy()

conflict_count = len(collision_df)
print(f"💥 漏斗 3 (致命矛盾剔除)：发现并剔除了 {conflict_count:,} 行数值矛盾撞车数据！")

# ================= 6. 分装输出至 Temp_data =================
print("\n💾 正在保存极净映射长表与审计日志...")

# 6.1 导出矛盾撞车审计表
if conflict_count > 0:
    collision_df = collision_df.sort_values(by=['患者编号', '报告时间', '标准检验项名称'])
    collision_df.drop(columns=['Source_File', '原始脱水名称', '对齐后结果']).to_excel(collision_log_file, index=False)
    print(f"   [审计留存] 致命矛盾明细已安全隔离至: {collision_log_file}")

# 6.2 拆分并导出极致干净的映射表
for file in lab_files:
    sub_clean_df = clean_df[clean_df['Source_File'] == file].copy()
    
    # 用洗套好的 Float 数值覆盖老旧结果，保证输出纯净
    sub_clean_df['结果'] = sub_clean_df['对齐后结果']
    sub_clean_df = sub_clean_df.drop(columns=['Source_File', '原始脱水名称', '对齐后结果'])
    
    out_path = os.path.join(temp_dir, f"34_Mapped_Cleaned_{file}")
    sub_clean_df.to_excel(out_path, index=False)
    print(f"   [成功输出] 极净映射长表: {out_path} ({len(sub_clean_df):,} 行)")

print("\n🎉 长表映射与全量宽容防撞处理圆满完工！准备进入 Pivot 宽表转置阶段！")