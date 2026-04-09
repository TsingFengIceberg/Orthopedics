import pandas as pd
import os

# ================= 配置路径 =================
temp_dir = "../Temp_data"
modalities = ["CT", "MR", "XRay"]
# ============================================

print("🚀 开始按指定逻辑提取细粒度排查表...\n")

for mod in modalities:
    file_14 = os.path.join(temp_dir, f"14_Unmatched_{mod}_Metadata_a.csv")
    file_10 = os.path.join(temp_dir, f"10_{mod}_Metadata_Clean.csv")
    
    if not os.path.exists(file_14) or not os.path.exists(file_10):
        print(f"⚠️ 找不到 {mod} 的相关文件，跳过。")
        continue
        
    print(f"📊 正在处理 {mod} 模态...")
    
    # 1. 读取两张表的数据
    df_unmatched = pd.read_csv(file_14, low_memory=False)
    df_original = pd.read_csv(file_10, low_memory=False)
    
    # 2. 动态定位 SeriesDescription 字段列名（防止不同模态有细微差别）
    sd_cols = [c for c in df_unmatched.columns if 'SeriesDescription' in c]
    if not sd_cols:
        print(f"⚠️ 未找到 SeriesDescription 字段，跳过 {mod}。")
        continue
    sd_col = sd_cols[0]
    
    # 3. 截取前三列：Image_Data_ID, Image_Name, SeriesDescription
    result_df = df_unmatched[['Image_Data_ID', 'Image_Name', sd_col]].copy()
    
    # 4. 统计原始数据(10_表)中每个 Image_Data_ID 的总行数 -> 第四列
    total_counts = df_original.groupby('Image_Data_ID').size().reset_index(name='原始总数量')
    
    # 5. 统计当前不符合表(14_表)中每个 Image_Data_ID 的总行数 -> 第五列
    unmatched_counts = df_unmatched.groupby('Image_Data_ID').size().reset_index(name='当前不符合数量')
    
    # 6. 将统计结果合并（左连接）回 result_df
    result_df = pd.merge(result_df, total_counts, on='Image_Data_ID', how='left')
    result_df = pd.merge(result_df, unmatched_counts, on='Image_Data_ID', how='left')
    
    # 7. 计算第六列：暂时正常数量 = 原始总数量 - 当前不符合数量
    result_df['暂时正常数量'] = result_df['原始总数量'] - result_df['当前不符合数量']
    
    # 导出最终表
    out_file = os.path.join(temp_dir, f"17_Unmatched_Detail_{mod}.csv")
    result_df.to_csv(out_file, index=False, encoding='utf-8-sig')
    
    print(f"   ✅ 完成！共生成 {len(result_df)} 行。")
    print(f"   💾 已保存至: {out_file}\n")

print("🎉 所有模态处理完毕！请查看生成的 17_Unmatched_Detail 系列文件。")