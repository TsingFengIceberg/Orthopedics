import pandas as pd
import os

# 配置路径
temp_dir = "../Temp_data"
modalities = ["CT", "MR", "XRay"]

# 定义我们要观察的“部位相关”候选字段
# 注意：代码会自动匹配包含这些关键字的列名，因为原始列名带有 (Tag) 前缀
target_keywords = ['BodyPartExamined', 'SeriesDescription', 'StudyDescription', 'ReceiveCoilName']

print("🔍 正在启动全模态部位信息大普查...\n")

for mod in modalities:
    file_path = os.path.join(temp_dir, f"10_{mod}_Metadata_Clean.csv")
    if not os.path.exists(file_path):
        print(f"⚠️ 未找到文件: {file_path}，跳过。")
        continue
    
    print(f"📊 --- {mod} 模态部位分布报告 ---")
    df = pd.read_csv(file_path, low_memory=False)
    
    # 找出当前表中存在的候选列
    available_cols = []
    for kw in target_keywords:
        match = [c for c in df.columns if kw in c]
        if match:
            available_cols.append(match[0])
    
    # 对每一个候选列进行频次统计
    for col in available_cols:
        print(f"\n【字段: {col}】")
        # fillna('MISSING') 确保空值也能被统计到
        counts = df[col].fillna('EMPTY_VALUE').value_counts()
        
        # 打印前 15 个最常见的取值（通常最常见的就是我们要的部位）
        print(f"{'取值 (Value)':<40} | {'频次 (Count)':<10}")
        print("-" * 55)
        for val, cnt in counts.head(15).items():
            print(f"{str(val)[:40]:<40} | {cnt:<10}")
        
        unique_count = len(counts)
        print(f"--- 该字段共有 {unique_count} 种不同取值 ---")
    
    print("\n" + "="*60 + "\n")

print("✅ 普查完毕！请根据打印结果观察哪些值代表“无关部位”。")