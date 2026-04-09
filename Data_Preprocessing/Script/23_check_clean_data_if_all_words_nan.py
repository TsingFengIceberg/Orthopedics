import pandas as pd
import os

# ================= 配置路径 =================
temp_dir = "../Temp_data"
modalities = ["CT", "MR", "XRay"]

target_keywords = ['BodyPartExamined', 'SeriesDescription', 'StudyDescription', 'ReceiveCoilName']

# 定义什么算作“空”
EMPTY_FLAGS = ['NAN', 'EMPTY_VALUE', 'NONE', 'NULL', '']
# ============================================

def is_all_empty(row, cols):
    """判断指定的所有列是否全部为空"""
    for col in cols:
        val = str(row[col]).strip().upper()
        # 只要有一列不是空值，就说明不是“全空数据”
        if val not in EMPTY_FLAGS:
            return False
    # 如果循环走完都没 return False，说明全都是空
    return True

print("🔍 启动保底逻辑：校验【最终留存的合规数据】中是否存在全空盲盒...\n")

for mod in modalities:
    file_10 = os.path.join(temp_dir, f"10_{mod}_Metadata_Clean.csv")
    file_23 = os.path.join(temp_dir, f"23_New_Unmatched_{mod}_Metadata_Full.csv")
    
    if not os.path.exists(file_10) or not os.path.exists(file_23):
        print(f"⚠️ 找不到 {mod} 的相关原始/未匹配文件，跳过。")
        continue
        
    # 1. 加载数据
    df_10 = pd.read_csv(file_10, low_memory=False)
    df_23 = pd.read_csv(file_23, low_memory=False)
    
    # 2. 获取留存的正确数据 ( df_10 减去 df_23 )
    # 通过 Image_Data_ID 和 Image_Name 作为主键进行左连接排他过滤（Anti-Join）
    keys = ['Image_Data_ID', 'Image_Name']
    
    # 确保键是字符串格式，防止类型不匹配导致 merge 失败
    for k in keys:
        df_10[k] = df_10[k].astype(str)
        df_23[k] = df_23[k].astype(str)
        
    merged = pd.merge(df_10, df_23[keys], on=keys, how='left', indicator=True)
    # 选出只在左表 (10_Clean) 中存在的数据，这就是我们要的合规留存数据
    df_retained = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge']).copy()
    
    # 3. 动态定位当前模态存在的语义列 (CT/XRay 3列，MR 4列)
    available_cols = []
    for kw in target_keywords:
        match = [c for c in df_retained.columns if kw in c]
        if match:
            available_cols.append(match[0])
            
    # 4. 执行“全空”校验
    mask_all_empty = df_retained.apply(lambda row: is_all_empty(row, available_cols), axis=1)
    df_bad_empty = df_retained[mask_all_empty].copy()
    
    bad_count = len(df_bad_empty)
    
    print(f"📊 --- {mod} 模态保底校验 ---")
    print(f"   原始总数据: {len(df_10)} 行")
    print(f"   最终留存 (合规) 数据: {len(df_retained)} 行")
    print(f"   校验列数: {len(available_cols)} 列 {available_cols}")
    
    if bad_count > 0:
        print(f"   ❌ 警报！在留存数据中发现了 {bad_count} 条语义全空的漏网之鱼！")
        # 导出这些出错的全空数据
        export_cols = ['Image_Data_ID', 'Image_Name'] + available_cols
        out_file = os.path.join(temp_dir, f"23_Retained_But_Empty_{mod}.csv")
        df_bad_empty[export_cols].to_csv(out_file, index=False, encoding='utf-8-sig')
        print(f"   💾 异常全空数据已保存至: {out_file}")
    else:
        print(f"   ✅ 安全！留存的 {len(df_retained)} 条数据中，没有任何一条是全空盲盒。逻辑绝对闭环！")
        
    print("\n" + "="*80 + "\n")

print("🏁 保底校验完毕！")