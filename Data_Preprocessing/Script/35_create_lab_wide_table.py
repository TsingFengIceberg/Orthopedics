import os
import pandas as pd
import numpy as np

# ================= 配置路径 =================
temp_dir = '../Temp_data'
# 动态匹配我们上一轮生成的干净底表
lab_files = [f'34_Mapped_Cleaned_Lab_Results_{i}.xlsx' for i in range(1, 4)]
output_file = os.path.join(temp_dir, '35_Lab_Wide_Table.csv')

print("🚀 启动【机器学习级：事件驱动大宽表转置引擎】...\n")

# ================= 1. 加载并合并所有干净的长表 =================
all_dfs = []
for file in lab_files:
    file_path = os.path.join(temp_dir, file)
    if os.path.exists(file_path):
        print(f"📂 正在加载无冲突长表: {file}")
        all_dfs.append(pd.read_excel(file_path))

if not all_dfs:
    raise FileNotFoundError("⚠️ 找不到任何 34 号开头的清洗后文件，请检查路径！")

df_clean = pd.concat(all_dfs, ignore_index=True)
print(f"✅ 成功合并纯净数据，共计 {len(df_clean):,} 行长表记录。")

# ================= 2. 核心特征工程：构建特征列名 =================
print("🏷️ 正在构建高维特征列名 (大项_小项)...")
# 策略：将"大项目名称"和"标准小项名称"无缝拼接，例如生成 "生化全套_葡萄糖"
# 这样不仅能区分同名小项（如急诊白细胞 vs 普通白细胞），也能极大增强模型的理解力
df_clean['大项'] = df_clean['项目名称'].astype(str).str.strip()
df_clean['小项'] = df_clean['标准检验项名称'].astype(str).str.strip()
df_clean['特征名称'] = df_clean['大项'] + '_' + df_clean['小项']

# ================= 3. 护城河：处理无时间数据的“黑洞陷阱” =================
print("🛡️ 正在铺设无时间数据保护网 (防止 Pandas 吞噬 NaN 索引)...")
# 发临时护照：把 NaN 或空白字符替换为特殊标识
df_clean['报告时间_安全'] = df_clean['报告时间'].fillna('【无时间记录】')
df_clean['报告时间_安全'] = df_clean['报告时间_安全'].replace('', '【无时间记录】').replace('nan', '【无时间记录】')

# ================= 4. 执行终极 Pivot (长表拍扁拉宽) =================
print("🔄 正在执行高维矩阵转置 (Pivot)... 正在拍扁拉宽中，请稍候...")

# index: 行的主键 (定义了"一行"到底代表什么：同一个人在同一个时刻)
# columns: 列的维度 (定义了"列"代表什么：所有的特征名称)
# values: 格子里的具体数值
# aggfunc='first': 因为我们在34号脚本里已经彻底绝杀了冲突，这里绝对是 1对1 完美映射，取 first 即可安全填入
wide_df = df_clean.pivot_table(
    index=['患者编号', '报告时间_安全'],
    columns='特征名称',
    values='结果',
    aggfunc='first'
)

# ================= 5. 矩阵形态重构与收尾 =================
print("🧹 正在展平特征矩阵并恢复真实时间戳...")

# pivot 出来的表，行名(index)是嵌套的，我们需要把它展平为普通的列
wide_df = wide_df.reset_index()

# 过河拆桥：把我们刚才发的“临时护照”替换回真实的 Pandas 空值(NaN)
wide_df['报告时间'] = wide_df['报告时间_安全'].replace('【无时间记录】', np.nan)
wide_df = wide_df.drop(columns=['报告时间_安全'])

# 强迫症排版：把'患者编号'和'报告时间'牢牢钉在表格的最左侧前两列
feature_cols = [c for c in wide_df.columns if c not in ['患者编号', '报告时间']]
# 顺便给特征列按首字母排个序，强迫症福音
feature_cols = sorted(feature_cols) 
final_cols = ['患者编号', '报告时间'] + feature_cols
wide_df = wide_df[final_cols]

# ================= 6. 导出最终 ML-Ready 宽表 =================
print(f"💾 正在保存最终稀疏大宽表...")
print(f"   📊 降维后矩阵形态：{wide_df.shape[0]:,} 个独立事件(行) × {wide_df.shape[1]:,} 个特征维度(列)")

# 使用 utf-8-sig 编码，保证即使你用 Excel 强行打开 CSV 也绝对不会中文乱码
wide_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n🎉 伟大胜利！极其干净的 ML-Ready 大宽表已成功生成至：{output_file}")