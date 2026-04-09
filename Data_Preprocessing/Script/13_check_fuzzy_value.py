import pandas as pd
import os

# 配置路径
input_dir = "../Temp_data"
# 模糊关注点
fuzzy_parts = ['CHEST', 'NECK', 'ABDOMEN', 'HEAD', 'EMPTY_VALUE']

for mod in ["CT", "MR"]:
    file_path = os.path.join(input_dir, f"10_{mod}_Metadata_Clean.csv")
    if not os.path.exists(file_path): continue
    
    print(f"\n🔍 === {mod} 模态：模糊部位深度采样分析 ===")
    df = pd.read_csv(file_path, low_memory=False)
    
    # 获取列名
    bp_col = [c for c in df.columns if 'BodyPartExamined' in c][0]
    sd_col = [c for c in df.columns if 'SeriesDescription' in c][0]
    
    for part in fuzzy_parts:
        # 筛选
        subset = df[df[bp_col].fillna('EMPTY_VALUE').str.upper() == part]
        
        if not subset.empty:
            total_count = len(subset)
            print(f"\n📌 标注部位: [{part}] (样本量: {total_count})")
            print(f"该标注下【序列描述】出现频率最高的前 10 种：")
            print("-" * 50)
            # 统计具体的描述文字
            desc_counts = subset[sd_col].fillna('NULL_DESC').value_counts().head(10)
            for desc, cnt in desc_counts.items():
                pct = (cnt / total_count) * 100
                print(f" - {str(desc):<35} | {cnt:<8} ({pct:>5.1f}%)")
        else:
            print(f"\n📌 标注部位: [{part}] -> 未发现数据。")

print("\n✅ 采样完毕！请根据描述内容判断是否需要保留。")