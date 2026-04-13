import os
import pandas as pd
import pydicom
from tqdm import tqdm

# ================= 配置路径 =================
raw_dicom_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS'
temp_dir = '../Temp_data'
os.makedirs(temp_dir, exist_ok=True)

# 输出的两个文件
out_raw_list_csv = os.path.join(temp_dir, '44_Absolute_Raw_DICOM_List.csv')
out_stats_csv = os.path.join(temp_dir, '44_Modality_Distribution_Stats.csv')

print("🚀 [44号] 启动 DICOM 物理硬盘全量快照引擎...\n")

# ================= 1. 执行物理探针扫描 =================
print("🔍 正在穿透硬盘目录，执行极速无差别 DICOM 头文件读取...")

records = []
error_files = 0
missing_tag_files = 0

# 获取所有的 MODALITYID 文件夹
modality_folders = [d for d in os.listdir(raw_dicom_dir) if os.path.isdir(os.path.join(raw_dicom_dir, d))]

# 遍历每个文件夹（带进度条）
for mod_id in tqdm(modality_folders, desc="全量目录扫描进度"):
    folder_path = os.path.join(raw_dicom_dir, mod_id)
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        
        # 只处理文件
        if not os.path.isfile(file_path): 
            continue
            
        try:
            # 🌟 斩首行动：stop_before_pixels=True，只读几十字节的文本头，极速！
            # force=True 强制读取，即使缺少标准 DICOM 前缀
            ds = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
            
            # 提取 Modality 标签 (0008, 0060)
            if 'Modality' in ds:
                mod_value = str(ds.Modality).strip().upper()
            else:
                mod_value = '【标签缺失(MISSING)】'
                missing_tag_files += 1
                
            records.append({
                '文件夹名称(MODALITYID)': mod_id,
                '物理文件名': file_name,
                '底层模态标签(Modality)': mod_value
            })
            
        except Exception as e:
            # 如果彻底读碎了（比如混入了 .DS_Store 或 txt 文本）
            records.append({
                '文件夹名称(MODALITYID)': mod_id,
                '物理文件名': file_name,
                '底层模态标签(Modality)': '【非合法DICOM文件(ERROR)】'
            })
            error_files += 1

# ================= 2. 转换为 DataFrame 并保存全量底表 =================
df_all = pd.DataFrame(records)

print(f"\n✅ 硬盘扫描结束！")
print(f"   ▪ 总计发现物理文件: {len(df_all):,} 个")
print(f"   ▪ 其中标签缺失文件: {missing_tag_files:,} 个")
print(f"   ▪ 其中非DICOM损坏文件: {error_files:,} 个\n")

print(f"💾 正在保存全量快照大表 (一张图一行)...")
df_all.to_csv(out_raw_list_csv, index=False, encoding='utf-8-sig')

# ================= 3. 统计全院模态分布情况 (以文件为颗粒度) =================
print("📊 正在统计底层 Modality 字段的绝对分布比例...")

# 统计每个模态标签出现了多少次
df_stats = df_all['底层模态标签(Modality)'].value_counts().reset_index()
df_stats.columns = ['底层模态标签', '物理图片数量']

# 计算占比
total_files = len(df_all)
df_stats['占比(%)'] = (df_stats['物理图片数量'] / total_files * 100).round(2)

print("\n" + "="*50)
print("🏆 [全院 DICOM 物理文件模态分布排行榜]")
print("="*50)
# 打印前 15 名，防止终端刷屏
print(df_stats.head(15).to_string(index=False))
print("="*50)

# 导出完整的统计表
df_stats.to_csv(out_stats_csv, index=False, encoding='utf-8-sig')

print(f"\n🎉 盘点完成！")
print(f"   📄 全量明细表已保存至: {out_raw_list_csv}")
print(f"   📈 分布统计表已保存至: {out_stats_csv}")
print("\n💡 下一步建议：请将终端打印出的【模态分布排行榜】拍照发给医生，用最底层的数据跟他们探讨 CT 去哪了。")