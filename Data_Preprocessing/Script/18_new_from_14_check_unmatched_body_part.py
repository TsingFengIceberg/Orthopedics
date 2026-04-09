import pandas as pd
import os

# ================= 配置路径 =================
temp_dir = "../Temp_data"
modalities = ["CT", "MR", "XRay"]

# 【强约束】脊柱白名单
WHITE_LIST = [
    'SPINE', 'LSPINE', 'TSPINE', 'CSPINE', 'L-S', 'T-L', 'L-SPINE', 'T-SPINE', 'C-SPINE',
    '椎', 'ZHUI', 
    'BONE', 'STIR', 'DIXON', 'SAG', 'COR', # 注意：这里把之前的 COR 也加进来了
    'SPINEARRAY', 'AIM_SPINE', 'CTSP_ADAPTER',
    'T6-L3', 'ji zhu',
    '位',
    '3D_5mm COR_1',
    '3D_Batch',
    '1.25mm std',
    '1.5 x 1.0',
    '1.5 x 1.2'
]

target_keywords = ['BodyPartExamined', 'SeriesDescription', 'StudyDescription', 'ReceiveCoilName']
# ============================================

def check_match(row, cols):
    """强约束匹配：只要任意一个字段包含核心白名单关键词，返回 True"""
    for col in cols:
        val = str(row[col]).upper()
        if val == 'NAN' or val == 'EMPTY_VALUE':
            continue
        # 将关键词转大写后匹配，解决大小写遗漏问题
        if any(kw.upper() in val for kw in WHITE_LIST):
            return True
    return False

print("🚀 开始反向筛选：提取【不符合】强脊柱约束的数据 (全量打印版)...\n")

for mod in modalities:
    in_file = os.path.join(temp_dir, f"10_{mod}_Metadata_Clean.csv")
    if not os.path.exists(in_file):
        continue
    
    df = pd.read_csv(in_file, low_memory=False)
    initial_count = len(df)
    
    # 定位实际列名
    available_cols = []
    for kw in target_keywords:
        match = [c for c in df.columns if kw in c]
        if match:
            available_cols.append(match[0])
    
    # 筛选【不符合】条件的行
    matched_mask = df.apply(lambda row: check_match(row, available_cols), axis=1)
    df_unmatched = df[~matched_mask].copy()
    
    unmatched_count = len(df_unmatched)
    
    # 导出不符合的数据表
    out_file = os.path.join(temp_dir, f"18_New_Unmatched_{mod}_Metadata_Full.csv")
    df_unmatched.to_csv(out_file, index=False, encoding='utf-8-sig')
    
    print(f"📊 --- {mod} 模态反向统计 ---")
    print(f"   初始总数: {initial_count}")
    print(f"   符合强约束数: {initial_count - unmatched_count}")
    print(f"   不符合(已入表)数: {unmatched_count}")
    print(f"   💾 不符合表已保存至: {out_file}")

    # 对提取出的“不符合”数据进行字段分布统计
    print(f"\n🧐 深度普查 [ {mod} ] 不符合数据中的字段分布:")
    for col in available_cols:
        print(f"\n   【字段: {col}】")
        counts = df_unmatched[col].fillna('EMPTY_VALUE').value_counts()
        print(f"      {'取值 (Value)':<45} | {'频次 (Count)':<10}")
        print("      " + "-" * 60)
        
        # 【关键修改】：去掉了 .head(15)，改为全量打印
        for val, cnt in counts.items():
            print(f"      {str(val)[:45]:<45} | {cnt:<10}")
            
        print(f"      --- 该字段共有 {len(counts)} 种不同取值 ---")
    
    print("\n" + "="*80 + "\n")

print("✅ 全量反向普查完毕！请检查这批彻底的“垫底”数据中是否还有骨科相关的词汇。")