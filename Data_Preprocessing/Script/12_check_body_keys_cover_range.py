import pandas as pd
import os

# 配置路径
temp_dir = "../Temp_data"
modalities = ["CT", "MR", "XRay"]

# 排序后的候选字段关键字（按辨识强度排序）
# 注意：MR 包含线圈，CT/XRay 只有前三个
order_ct_xray = ['BodyPartExamined', 'SeriesDescription', 'StudyDescription']
order_mr = ['BodyPartExamined', 'SeriesDescription', 'StudyDescription', 'ReceiveCoilName']

print("📈 正在进行【部位辨识字段】增量覆盖率分析...\n")

for mod in modalities:
    file_path = os.path.join(temp_dir, f"10_{mod}_Metadata_Clean.csv")
    if not os.path.exists(file_path):
        continue
    
    df = pd.read_csv(file_path, low_memory=False)
    total_rows = len(df)
    current_order = order_mr if mod == "MR" else order_ct_xray
    
    print(f"📊 --- {mod} 模态分析 (总行数: {total_rows}) ---")
    
    # 获取实际列名
    actual_cols = []
    for kw in current_order:
        match = [c for c in df.columns if kw in c]
        if match:
            actual_cols.append(match[0])
    
    # 增量计算并集
    # combined_mask 记录只要其中一个字段不为空的行
    combined_mask = pd.Series([False] * total_rows)
    
    for i, col in enumerate(actual_cols):
        col_mask = df[col].notna() & (df[col].astype(str).str.upper() != 'EMPTY_VALUE')
        combined_mask = combined_mask | col_mask
        
        covered_count = combined_mask.sum()
        covered_pct = (covered_count / total_rows) * 100
        
        step_name = f"前 {i+1} 个字段并集"
        print(f" {step_name:<15} | 覆盖数: {covered_count:<10} | 覆盖率: {covered_pct:>6.2f}%")
        print(f"   (新加入字段: {col})")
        
    uncovered = total_rows - combined_mask.sum()
    print(f" ❌ 最终仍有 {uncovered} 行数据没有任何部位描述信息 ({(uncovered/total_rows)*100:.2f}%)")
    print("-" * 60)

print("\n✅ 分析完毕！建议根据覆盖率结果，决定最终的过滤逻辑。")