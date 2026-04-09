import os
import pydicom
import pandas as pd
import json
from tqdm import tqdm

# ================= 配置区 =================
base_dir = "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS"
output_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"
temp_jsonl = "../Temp_data/03_DICOM_temp_checkpoint.jsonl"  # 实时存储的中间件（保险箱）
error_log = "../Temp_data/03_DICOM_error_log.txt"           # 错误黑名单
# ==========================================

def get_processed_files(jsonl_path):
    """【保险机制 2】获取已经处理过的文件列表，用于断点续传"""
    processed = set()
    if os.path.exists(jsonl_path):
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 使用 Image_Data_ID 和 Image_Name 的组合作为唯一标识
                    identifier = f"{data.get('Image_Data_ID')}/{data.get('Image_Name')}"
                    processed.add(identifier)
                except:
                    continue
    return processed

def robust_extract():
    print("🔍 阶段一：扫描文件夹，构建任务队列...")
    all_dcm_paths = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith('.dcm'):
                all_dcm_paths.append(os.path.join(root, file))
                
    total_files = len(all_dcm_paths)
    if total_files == 0:
        print("⚠️ 未找到任何 .dcm 文件！")
        return

    # 获取已经处理过的断点记录
    processed_identifiers = get_processed_files(temp_jsonl)
    
    # 过滤出还需要处理的文件
    pending_files = []
    for path in all_dcm_paths:
        img_id = os.path.basename(os.path.dirname(path))
        img_name = os.path.basename(path)
        if f"{img_id}/{img_name}" not in processed_identifiers:
            pending_files.append(path)
            
    skip_count = total_files - len(pending_files)
    print(f"✅ 扫描完毕！总文件: {total_files} | 已处理: {skip_count} | 本次需处理: {len(pending_files)}\n")

    if not pending_files:
        print("🎉 所有文件均已处理完毕，直接进入表格生成阶段！")
    else:
        print("🚀 阶段二：开始流式提取 (实时落盘，不怕中断)...")
        # 以追加模式 (a) 打开 JSONL 文件
        with open(temp_jsonl, 'a', encoding='utf-8') as f_out, \
             open(error_log, 'a', encoding='utf-8') as f_err:
            
            for path in tqdm(pending_files, desc="提取进度", unit="file"):
                try:
                    image_data_id = os.path.basename(os.path.dirname(path))
                    image_name = os.path.basename(path)
                    
                    row_data = {
                        "Image_Data_ID": image_data_id,
                        "Image_Name": image_name
                    }
                    
                    # 极速且安全读取元数据
                    ds = pydicom.dcmread(path, stop_before_pixels=True)
                    
                    for elem in ds:
                        tag_str = str(elem.tag)
                        name = elem.keyword if elem.keyword else "Private_or_Unknown"
                        col_name = f"{tag_str} [{name}]"
                        
                        val = elem.value
                        
                        # 【保险机制 1.5】值域截断，防止脏数据爆内存
                        if elem.VR == 'SQ':
                            val_str = f"<Sequence: {len(val)} items>"
                        elif isinstance(val, bytes):
                            val_str = f"<Bytes: length {len(val)}>" if len(val) > 100 else str(val)
                        else:
                            val_str = str(val)
                            if len(val_str) > 1000:
                                val_str = val_str[:997] + "..."
                        
                        row_data[col_name] = val_str
                    
                    # 【保险机制 1】流式落盘：处理完一个文件，立刻作为一行 JSON 写入硬盘
                    f_out.write(json.dumps(row_data, ensure_ascii=False) + '\n')
                    
                except Exception as e:
                    # 【保险机制 3】异常隔离：出错不崩溃，记入黑名单
                    f_err.write(f"ERROR | {path} | {str(e)}\n")

    # ==========================================
    # 阶段三：将安全的 JSONL 中间件转换为最终大宽表
    # ==========================================
    print("\n📦 阶段三：正在将中间数据合并，构建最终的稀疏大宽表...")
    # Pandas 读取 JSONL 非常高效，会自动把缺失的字段用 NaN 填补
    try:
        df = pd.read_json(temp_jsonl, lines=True)
        
        # 整理列顺序
        fixed_cols = ["Image_Data_ID", "Image_Name"]
        dynamic_cols = sorted([c for c in df.columns if c not in fixed_cols])
        final_cols = fixed_cols + dynamic_cols
        
        df = df[final_cols]
        
        print(f"💾 正在导出 CSV: {output_csv} ...")
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
        print("-" * 50)
        print(f"🎉 任务圆满完成！最终大表尺寸: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"💡 提示: 如果你确认 CSV 无误，可以手动删除临时文件 {temp_jsonl}")
        
    except Exception as e:
        print(f"❌ 生成最终 CSV 时发生错误: {e}")
        print(f"⚠️ 别担心，你的数据已经安全保存在 {temp_jsonl} 中，随时可以重新转换。")

if __name__ == "__main__":
    robust_extract()