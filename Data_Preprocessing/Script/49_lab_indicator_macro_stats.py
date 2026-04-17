import pandas as pd
import os

# ================= 配置路径 =================
temp_dir = '../Temp_data'
input_file = os.path.join(temp_dir, '35_Lab_Wide_Table.csv')
output_file = os.path.join(temp_dir, '49_Lab_Indicator_Macro_Stats.xlsx')

print("🚀 [49号] 启动【检验指标宏观统计引擎】(频次与患者覆盖度分析)...\n")

# ================= 1. 加载大宽表 =================
print(f"📂 正在加载事件驱动大宽表: 35_Lab_Wide_Table.csv (表较大，请稍候)...")
# 使用 low_memory=False 防止宽表列太多推断类型时报警告
df = pd.read_csv(input_file, low_memory=False)

print(f"✅ 加载成功！大宽表共计 {len(df):,} 行事件记录，{len(df.columns)} 个维度。")

# ================= 2. 区分主键与特征列 =================
id_col = '患者编号'
time_col = '报告时间'

# 提取所有的检验指标列 (去掉前两列的主键)
feature_cols = [col for col in df.columns if col not in [id_col, time_col]]
print(f"📊 发现 {len(feature_cols)} 个独立的检验指标特征。")

# ================= 3. 统计每个指标的频次与患者数 =================
print("⏳ 正在逐列进行宏观聚合统计 (计算总频次与覆盖患者数)...")

stats_data = []

for col in feature_cols:
    # 筛选出该指标“非空”的有效行
    valid_rows = df[df[col].notna()]
    
    # 计算总检验次数 (即非空行的绝对数量)
    total_tests = len(valid_rows)
    
    # 计算检验过的独立患者数 (对这些非空行里的“患者编号”去重计数)
    unique_patients = valid_rows[id_col].nunique() if total_tests > 0 else 0
    
    stats_data.append({
        '检验指标名称': col,
        '检验总次数': total_tests,
        '检验患者数': unique_patients
    })

# ================= 4. 生成报告并导出 =================
df_stats = pd.DataFrame(stats_data)

# 排序逻辑：优先按照“覆盖患者数”降序排，患者数一样的再按“总检验次数”降序排
# 因为在做 AI 模型时，患者覆盖度越广的指标，作为基础特征的优先级越高
df_stats.sort_values(by=['检验患者数', '检验总次数'], ascending=[False, False], inplace=True)

print(f"💾 正在导出宏观统计报告至: {output_file}")
df_stats.to_excel(output_file, index=False)

print("\n🏆 宏观盘点 Top 10 核心指标预览：")
print("-" * 60)
print(df_stats.head(10).to_string(index=False))
print("-" * 60)

print(f"\n🎉 49号脚本运行完毕！")
print("💡 下一步建议：打开这个 Excel，你可以一眼看出哪些是全院必查的常规指标（比如血常规），哪些是罕见的特检指标，这将极大帮助你后续筛选入模特征！")