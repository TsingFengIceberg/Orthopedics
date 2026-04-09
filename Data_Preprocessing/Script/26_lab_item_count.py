import os
import pandas as pd

# ================= 配置路径 =================
data_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'
temp_dir = '../Temp_data' # 可以放在你之前的临时文件夹
os.makedirs(temp_dir, exist_ok=True)

lab_files = ['Lab_Results_1.xlsx', 'Lab_Results_2.xlsx', 'Lab_Results_3.xlsx']

print("🚀 开始遍历检验表，进行全量字段摸底（探路模式）...\n")

# 用于存储所有检验项频率的字典
item_counter = {}
total_rows_processed = 0

for file in lab_files:
    file_path = os.path.join(data_dir, file)
    if not os.path.exists(file_path):
        print(f"  ⚠️ 未找到文件 {file}，跳过。")
        continue
        
    print(f"📂 正在扫描: {file} ...")
    
    # 为了节省内存并提高速度，只读取需要的两列
    # 假设你的列名是 '分析明细' 和 '项目名称'，如果报错请根据实际表头调整
    try:
        df = pd.read_excel(file_path, usecols=['项目名称', '分析明细'])
    except ValueError:
        # 如果找不到这两列，尝试备用读取全表再看列名
        print(f"  ⚠️ {file} 中未找到指定的列名，请检查表头是否带有空格！")
        continue
        
    # 清理一下首尾空格，防止 "血常规 " 和 "血常规" 被当成两个东西
    df['项目名称'] = df['项目名称'].astype(str).str.strip()
    df['分析明细'] = df['分析明细'].astype(str).str.strip()
    
    # 过滤掉空行 (把 'nan' 字符串的踢掉)
    df = df[(df['项目名称'] != 'nan') & (df['分析明细'] != 'nan')]
    
    # 组合名称，例如："血常规_白细胞数"
    combined_names = df['项目名称'] + " - " + df['分析明细']
    
    # 统计词频并合并到总字典
    counts = combined_names.value_counts().to_dict()
    for name, count in counts.items():
        item_counter[name] = item_counter.get(name, 0) + count
        
    total_rows_processed += len(df)
    print(f"  ✅ {file} 扫描完毕，本表有效行数: {len(df)}")

print("\n" + "="*50)
print(f"🏁 扫描结束！共处理检验记录 {total_rows_processed} 条。")

# 转换为 DataFrame 方便排序和导出
summary_df = pd.DataFrame(list(item_counter.items()), columns=['完整检验项 (项目 - 明细)', '出现总频次'])
# 按频次从高到低排序
summary_df.sort_values(by='出现总频次', ascending=False, inplace=True)

unique_count = len(summary_df)
print(f"💡 惊叹！所有患者加起来，一共产生了 【 {unique_count} 】 个不同的检验列！")

# 打印前 15 个最常见的检验项
print("\n🔥 出现频次最高的 Top 15 检验项：")
print(summary_df.head(15).to_string(index=False))

# 导出这个总表，这是你以后和医生开会讨论的“黄金清单”
out_file = os.path.join(temp_dir, '26_Lab_Items_Full_Dictionary.csv')
summary_df.to_csv(out_file, index=False, encoding='utf-8-sig')
print(f"\n💾 完整的《检验项目频次总字典》已导出至: {out_file}")
print("👉 建议动作：把这个 CSV 发给医生，让他们从中挑选出对课题有价值的项，剔除没用的项，这样能极大缩小宽表的体积！")