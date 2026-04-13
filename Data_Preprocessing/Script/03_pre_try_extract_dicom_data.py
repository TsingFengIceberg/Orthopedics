# import os
# import pydicom
# import pandas as pd
# import json
# from tqdm import tqdm

# # ================= 配置区 =================
# base_dir = "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS"
# output_csv = "../Temp_data/03_DICOM_Full_Sparse_Table.csv"
# temp_jsonl = "../Temp_data/03_DICOM_temp_checkpoint.jsonl"  # 实时存储的中间件（保险箱）
# error_log = "../Temp_data/03_DICOM_error_log.txt"           # 错误黑名单
# # ==========================================

# def get_processed_files(jsonl_path):
#     """【保险机制 2】获取已经处理过的文件列表，用于断点续传"""
#     processed = set()
#     if os.path.exists(jsonl_path):
#         with open(jsonl_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 try:
#                     data = json.loads(line)
#                     # 使用 Image_Data_ID 和 Image_Name 的组合作为唯一标识
#                     identifier = f"{data.get('Image_Data_ID')}/{data.get('Image_Name')}"
#                     processed.add(identifier)
#                 except:
#                     continue
#     return processed

# def robust_extract():
#     print("🔍 阶段一：扫描文件夹，构建任务队列...")
#     all_dcm_paths = []
#     for root, dirs, files in os.walk(base_dir):
#         for file in files:
#             if file.lower().endswith('.dcm'):
#                 all_dcm_paths.append(os.path.join(root, file))
                
#     total_files = len(all_dcm_paths)
#     if total_files == 0:
#         print("⚠️ 未找到任何 .dcm 文件！")
#         return

#     # 获取已经处理过的断点记录
#     processed_identifiers = get_processed_files(temp_jsonl)
    
#     # 过滤出还需要处理的文件
#     pending_files = []
#     for path in all_dcm_paths:
#         img_id = os.path.basename(os.path.dirname(path))
#         img_name = os.path.basename(path)
#         if f"{img_id}/{img_name}" not in processed_identifiers:
#             pending_files.append(path)
            
#     skip_count = total_files - len(pending_files)
#     print(f"✅ 扫描完毕！总文件: {total_files} | 已处理: {skip_count} | 本次需处理: {len(pending_files)}\n")

#     if not pending_files:
#         print("🎉 所有文件均已处理完毕，直接进入表格生成阶段！")
#     else:
#         print("🚀 阶段二：开始流式提取 (实时落盘，不怕中断)...")
#         # 以追加模式 (a) 打开 JSONL 文件
#         with open(temp_jsonl, 'a', encoding='utf-8') as f_out, \
#              open(error_log, 'a', encoding='utf-8') as f_err:
            
#             for path in tqdm(pending_files, desc="提取进度", unit="file"):
#                 try:
#                     image_data_id = os.path.basename(os.path.dirname(path))
#                     image_name = os.path.basename(path)
                    
#                     row_data = {
#                         "Image_Data_ID": image_data_id,
#                         "Image_Name": image_name
#                     }
                    
#                     # 极速且安全读取元数据
#                     ds = pydicom.dcmread(path, stop_before_pixels=True)
                    
#                     for elem in ds:
#                         tag_str = str(elem.tag)
#                         name = elem.keyword if elem.keyword else "Private_or_Unknown"
#                         col_name = f"{tag_str} [{name}]"
                        
#                         val = elem.value
                        
#                         # 【保险机制 1.5】值域截断，防止脏数据爆内存
#                         if elem.VR == 'SQ':
#                             val_str = f"<Sequence: {len(val)} items>"
#                         elif isinstance(val, bytes):
#                             val_str = f"<Bytes: length {len(val)}>" if len(val) > 100 else str(val)
#                         else:
#                             val_str = str(val)
#                             if len(val_str) > 1000:
#                                 val_str = val_str[:997] + "..."
                        
#                         row_data[col_name] = val_str
                    
#                     # 【保险机制 1】流式落盘：处理完一个文件，立刻作为一行 JSON 写入硬盘
#                     f_out.write(json.dumps(row_data, ensure_ascii=False) + '\n')
                    
#                 except Exception as e:
#                     # 【保险机制 3】异常隔离：出错不崩溃，记入黑名单
#                     f_err.write(f"ERROR | {path} | {str(e)}\n")

#     # ==========================================
#     # 阶段三：将安全的 JSONL 中间件转换为最终大宽表
#     # ==========================================
#     print("\n📦 阶段三：正在将中间数据合并，构建最终的稀疏大宽表...")
#     # Pandas 读取 JSONL 非常高效，会自动把缺失的字段用 NaN 填补
#     try:
#         df = pd.read_json(temp_jsonl, lines=True)
        
#         # 整理列顺序
#         fixed_cols = ["Image_Data_ID", "Image_Name"]
#         dynamic_cols = sorted([c for c in df.columns if c not in fixed_cols])
#         final_cols = fixed_cols + dynamic_cols
        
#         df = df[final_cols]
        
#         print(f"💾 正在导出 CSV: {output_csv} ...")
#         df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
#         print("-" * 50)
#         print(f"🎉 任务圆满完成！最终大表尺寸: {df.shape[0]} 行 × {df.shape[1]} 列")
#         print(f"💡 提示: 如果你确认 CSV 无误，可以手动删除临时文件 {temp_jsonl}")
        
#     except Exception as e:
#         print(f"❌ 生成最终 CSV 时发生错误: {e}")
#         print(f"⚠️ 别担心，你的数据已经安全保存在 {temp_jsonl} 中，随时可以重新转换。")

# if __name__ == "__main__":
#     robust_extract()


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
    """【保险机制 1】获取已经处理过的文件列表，用于断点续传"""
    processed = set()
    if os.path.exists(jsonl_path):
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    identifier = f"{data.get('Image_Data_ID')}/{data.get('Image_Name')}"
                    processed.add(identifier)
                except:
                    continue
    return processed

def robust_extract():
    print("🔍 阶段一：执行无差别物理扫描，构建任务队列...")
    all_file_paths = []
    
    # 🌟 无懈可击点 1：彻底废除 .endswith('.dcm') 判定！万物皆可入列！
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            all_file_paths.append(os.path.join(root, file))
                
    total_files = len(all_file_paths)
    if total_files == 0:
        print("⚠️ 目录为空，未找到任何文件！")
        return

    # 获取已经处理过的断点记录
    processed_identifiers = get_processed_files(temp_jsonl)
    
    # 过滤出还需要处理的文件
    pending_files = []
    for path in all_file_paths:
        img_id = os.path.basename(os.path.dirname(path))
        img_name = os.path.basename(path)
        if f"{img_id}/{img_name}" not in processed_identifiers:
            pending_files.append(path)
            
    skip_count = total_files - len(pending_files)
    print(f"✅ 扫描完毕！总物理文件: {total_files:,} | 已处理跳过: {skip_count:,} | 本次需处理: {len(pending_files):,}\n")

    if not pending_files:
        print("🎉 所有文件均已处理完毕，直接进入表格生成阶段！")
    else:
        print("🚀 阶段二：启动底层强力解析 (实时落盘，内存防爆)...")
        with open(temp_jsonl, 'a', encoding='utf-8') as f_out, \
             open(error_log, 'a', encoding='utf-8') as f_err:
            
            for path in tqdm(pending_files, desc="强力提取进度", unit="file"):
                image_data_id = os.path.basename(os.path.dirname(path))
                image_name = os.path.basename(path)
                
                try:
                    # 🌟 无懈可击点 2：暴力读取 + 斩首行动 (跳过像素，强制解析残缺头)
                    ds = pydicom.dcmread(path, stop_before_pixels=True, force=True)
                    
                    # 🌟 无懈可击点 3：真伪 DICOM 鉴别器
                    # force=True 可能会把 .txt 或 .DS_Store 强行解析成乱码
                    # 我们通过检查标准医学标签来验明正身。如果连这三个最基本的都没有，说明绝对是系统垃圾文件
                    if 'SOPClassUID' not in ds and 'Modality' not in ds and 'PatientID' not in ds:
                        continue # 静默跳过系统垃圾文件，不污染 error_log
                        
                except pydicom.errors.InvalidDicomError:
                    continue # 彻底无法解析的损坏文件，静默跳过
                except Exception as e:
                    # 解析发生了预料之外的严重错误，记入黑名单
                    f_err.write(f"ERROR_READ | {path} | {str(e)}\n")
                    continue

                # ================= 开始提取有效标签 =================
                row_data = {
                    "Image_Data_ID": image_data_id,
                    "Image_Name": image_name
                }
                
                try:
                    for elem in ds:
                        tag_str = str(elem.tag)
                        name = elem.keyword if elem.keyword else "Private_or_Unknown"
                        col_name = f"{tag_str} [{name}]"
                        
                        val = elem.value
                        
                        # 🌟 无懈可击点 4：极其稳健的内存防爆截断机制 (保留了你最初的智慧)
                        if elem.VR == 'SQ':
                            val_str = f"<Sequence: {len(val)} items>"
                        elif isinstance(val, bytes):
                            val_str = f"<Bytes: length {len(val)}>" if len(val) > 100 else str(val)
                        else:
                            val_str = str(val)
                            if len(val_str) > 1000:
                                val_str = val_str[:997] + "..."
                        
                        row_data[col_name] = val_str
                        
                    # 写入 JSONL 保险箱
                    f_out.write(json.dumps(row_data, ensure_ascii=False) + '\n')
                    
                except Exception as e:
                    f_err.write(f"ERROR_PARSE_TAGS | {path} | {str(e)}\n")

    # ==========================================
    # 阶段三：合并为终极稀疏大宽表
    # ==========================================
    print("\n📦 阶段三：正在将安全的 JSONL 中间件缝合为终极稀疏大宽表...")
    try:
        # chunkSize 读取防爆：如果几十万张图的 JSONL 太大，这里可以直接 pd.read_json
        df = pd.read_json(temp_jsonl, lines=True)
        
        # 整理列顺序：固定列放前面
        fixed_cols = ["Image_Data_ID", "Image_Name"]
        dynamic_cols = sorted([c for c in df.columns if c not in fixed_cols])
        final_cols = fixed_cols + dynamic_cols
        
        df = df[final_cols]
        
        print(f"💾 正在导出重磅 CSV: {output_csv} ...")
        # 这一步可能会耗时几分钟，因为表太大了
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
        print("-" * 50)
        print(f"🎉 伟大胜利！最终大表尺寸: {df.shape[0]:,} 行 × {df.shape[1]:,} 列")
        print(f"💡 提示: 如果 CSV 确认无误，你可以手动删除几十 GB 的临时文件 {temp_jsonl}")
        
    except ValueError as e:
        print(f"❌ 读取 JSONL 时发生错误 (可能是文件太空): {e}")
    except Exception as e:
        print(f"❌ 生成最终 CSV 时发生内存或写入错误: {e}")
        print(f"⚠️ 数据已安全保存在 {temp_jsonl} 中，可以考虑分块(chunk)读取或增加内存。")

if __name__ == "__main__":
    robust_extract()