import pandas as pd
import os

# ================= 配置路径 =================
temp_dir = "../Temp_data"
modalities = ["CT", "MR", "XRay"]

# 最新白名单
WHITE_LIST = [
    'SPINE', 'LSPINE', 'TSPINE', 'CSPINE', 'L-S', 'T-L', 'L-SPINE', 'T-SPINE', 'C-SPINE',
    '椎', 'ZHUI', 
    'BONE', 'STIR', 'DIXON', 'SAG', 'COR',
    'SPINEARRAY', 'AIM_SPINE', 'CTSP_ADAPTER',
    'T6-L3', 'ji zhu',
    '位',
    '3D_5mm COR_1',
    '3D_Batch',
    '1.25mm std', '1.25mm Std', '1.25mm stnd', '1.25mm Stnd', 
    '5mm std', '5mm Std', '5mm stnd', '5mm Stnd', 
    '1.5 x 1.0',
    '1.5 x 1.2',
    '3D_3mm SAR_1', '3D_3mm SAR_2'
]

# 最新黑名单
BLACK_LIST = [
    'LUNG', 
    'HEAD', 'BRAIN', 
    'DOSE REPORT', 
    'SCREEN SAVE', 
    'PROCESSED IMAGES', 
    '2D', 
    'tj tj', 
    'EMPTY_VALUE',
    'SCOUT',                          
    '3D_CT_VR_VOLREN_COLLECTION_1',   
    '3D_DEFAULT_1',
    'CHEST',
    'CTN0000049',
    '0915013854'                    
]

target_keywords = ['BodyPartExamined', 'SeriesDescription', 'StudyDescription', 'ReceiveCoilName']
# ============================================

def check_match(row, cols, word_list):
    """通用匹配函数：只要指定列中任意一项包含词表中的词，返回 True"""
    for col in cols:
        val = str(row[col]).upper()
        if val == 'NAN': 
            continue
        # 注意：EMPTY_VALUE 在我们这里被当作普通字符串处理，因为黑名单里有它
        if any(kw.upper() in val for kw in word_list):
            return True
    return False

print("🛡️ 启动终极兜底验证：寻找游离在规则之外的孤儿数据...\n")

for mod in modalities:
    in_file = os.path.join(temp_dir, f"10_{mod}_Metadata_Clean.csv")
    if not os.path.exists(in_file):
        continue
    
    df = pd.read_csv(in_file, low_memory=False)
    initial_count = len(df)
    
    # 动态定位当前模态实际存在的候选列
    available_cols = []
    for kw in target_keywords:
        match = [c for c in df.columns if kw in c]
        if match:
            available_cols.append(match[0])
            
    # 确立要导出的列：基础 ID 列 + 存在的语义列
    export_cols = ['Image_Data_ID', 'Image_Name'] + available_cols
    
    # 第一步：过白名单（筛出不包含白名单的数据）
    mask_white = df.apply(lambda row: check_match(row, available_cols, WHITE_LIST), axis=1)
    df_not_white = df[~mask_white].copy()
    count_after_white = len(df_not_white)
    
    # 第二步：过黑名单（在剩下的数据中，筛出也不包含黑名单的数据）
    mask_black = df_not_white.apply(lambda row: check_match(row, available_cols, BLACK_LIST), axis=1)
    df_orphans = df_not_white[~mask_black].copy()
    count_orphans = len(df_orphans)
    
    print(f"📊 --- {mod} 模态覆盖率验证 ---")
    print(f"   初始总行数: {initial_count}")
    print(f"   被白名单覆盖 (确认为保留): {initial_count - count_after_white}")
    print(f"   被黑名单覆盖 (确认为剔除): {count_after_white - count_orphans}")
    
    if count_orphans > 0:
        print(f"   ⚠️ 发现 {count_orphans} 条两边都不沾的【孤儿数据】！")
        # 仅保留需要的列并导出
        out_file = os.path.join(temp_dir, f"20_Orphan_Data_{mod}.csv")
        # 如果原始表里没有 Image_Name 等列，要防止报错
        final_export_cols = [c for c in export_cols if c in df_orphans.columns]
        df_orphans[final_export_cols].to_csv(out_file, index=False, encoding='utf-8-sig')
        print(f"   💾 孤儿数据已导出至: {out_file}")
        
        # 简单打印一下这些孤儿数据的 SeriesDescription，让你有个底
        sd_col = [c for c in available_cols if 'SeriesDescription' in c]
        if sd_col:
            print(f"\n   🧐 孤儿数据的 SeriesDescription 概览:")
            print(df_orphans[sd_col[0]].value_counts().head(10))
    else:
        print(f"   ✅ 完美！0 条孤儿数据，规则覆盖率 100%！")
        
    print("\n" + "="*70 + "\n")

print("🏁 验证流程结束！")