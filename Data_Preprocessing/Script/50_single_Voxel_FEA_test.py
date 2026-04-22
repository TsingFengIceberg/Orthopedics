import pandas as pd
import numpy as np
import os
import pydicom
import time
import cupy as cp
import h5py
import gc
from tqdm import tqdm
from scipy.ndimage import zoom
from collections import Counter

# ==========================================
# 1. 路径配置
# ==========================================
RAW_METADATA_PATH = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data/10_CT_Metadata_Clean.csv'
UNMATCHED_PATH = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data/22_New_Unmatched_CT_Metadata_Full.csv'
DICOM_BASE_DIR = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS'
OUTPUT_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'

# ==========================================
# 2. 核心算法工具
# ==========================================
def get_bounding_box(data, threshold=1e-5, margin=15):
    """智能边界盒算法"""
    coords = np.argwhere(data > threshold)
    if coords.size == 0:
        return None
    min_idx = coords.min(axis=0)
    max_idx = coords.max(axis=0)
    min_idx = np.maximum(min_idx - margin, 0)
    max_idx = np.minimum(max_idx + margin, np.array(data.shape) - 1)
    return min_idx, max_idx

def reconstruct_from_bbox(cropped_data, bbox, original_shape):
    """无损复原算法"""
    restored = np.zeros(original_shape, dtype=cropped_data.dtype)
    min_z, min_y, min_x = bbox[0]
    max_z, max_y, max_x = bbox[1]
    restored[min_z:max_z+1, min_y:max_y+1, min_x:max_x+1] = cropped_data
    return restored

# ==========================================
# 3. 主测试流程
# ==========================================
def run_ultimate_benchmark():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    df_raw = pd.read_csv(RAW_METADATA_PATH, low_memory=False)
    df_unmatched = pd.read_csv(UNMATCHED_PATH, low_memory=False)
    illegal_ids = set(df_unmatched['Image_Data_ID'].unique())
    target_id = [idx for idx in df_raw['Image_Data_ID'].unique() if idx not in illegal_ids][4]
    
    print(f"🚀 [终极测试] 启动！目标病人 ID: {target_id}")

    patient_dir = os.path.join(DICOM_BASE_DIR, str(target_id))
    dicom_files = sorted([os.path.join(patient_dir, f) for f in os.listdir(patient_dir) if f.endswith('.dcm')])
    raw_voxels = [pydicom.dcmread(f).pixel_array for f in tqdm(dicom_files, desc="[1/5] 加载 DICOM")]
    most_common = Counter([v.shape for v in raw_voxels]).most_common(1)[0][0]
    volume_low = np.stack([v for v in raw_voxels if v.shape == most_common]).astype(np.float32)

    print("\n[2/5] 正在执行 2.0x 空间重采样 (模拟 0.5mm 级极限精度)...")
    volume_high = zoom(volume_low, (2.0, 2.0, 2.0), order=1)
    original_shape = volume_high.shape
    
    print(f"\n[3/5] GPU 极限计算开始 (4090 D | 20轮演化)...")
    gpu_data = cp.asarray(volume_high)
    del volume_high
    gc.collect()

    for _ in range(20):
        _ = cp.fft.rfftn(gpu_data)
        gpu_data *= 0.999
    cp.cuda.Stream.null.synchronize()
    
    result_f32 = cp.asnumpy(gpu_data)
    
    print("\n[4/5] 正在执行智能裁剪与存储落盘测试...")
    
    # 1. 方案 0: 原始全量
    path_raw = os.path.join(OUTPUT_DIR, '50_benchmark_0_raw.npy')
    np.save(path_raw, result_f32)
    size_raw = os.path.getsize(path_raw) / (1024**3)

    # 2. 方案 1: ROI 裁剪 (找纸箱)
    bbox = get_bounding_box(result_f32, margin=15)
    min_idx, max_idx = bbox
    cropped_f32 = result_f32[min_idx[0]:max_idx[0]+1, min_idx[1]:max_idx[1]+1, min_idx[2]:max_idx[2]+1]
    
    path_crop = os.path.join(OUTPUT_DIR, '50_benchmark_1_crop.npy')
    np.save(path_crop, cropped_f32)
    size_crop = os.path.getsize(path_crop) / (1024**3)

    # 3. 方案 2: 终极 HDF5 方案 (装箱并压缩)
    path_h5 = os.path.join(OUTPUT_DIR, '50_benchmark_2_ultimate.h5')
    t_start = time.time()
    with h5py.File(path_h5, 'w') as f:
        f.create_dataset('stress_field', data=cropped_f32, compression="gzip", compression_opts=4)
        f.create_dataset('bbox_min', data=min_idx)
        f.create_dataset('bbox_max', data=max_idx)
        f.create_dataset('original_shape', data=np.array(original_shape))
    t_end = time.time()
    size_h5 = os.path.getsize(path_h5) / (1024**3)

    print("\n[5/5] 正在进行严格的数学无损验证...")
    with h5py.File(path_h5, 'r') as f:
        loaded_crop = f['stress_field'][:]
        loaded_bbox = (f['bbox_min'][:], f['bbox_max'][:])
        loaded_shape = tuple(f['original_shape'][:])
    
    restored_data = reconstruct_from_bbox(loaded_crop, loaded_bbox, loaded_shape)
    is_perfect = np.array_equal(result_f32, restored_data)

    print("\n" + "="*75)
    print("🏆 1497例全量并发症力学数据存储决策终极报告")
    print("="*75)
    print(f"🔹 原始矩阵尺寸: {original_shape}")
    print(f"🔹 裁剪后矩阵尺寸: {cropped_f32.shape}")
    print("-" * 75)
    print(f"{'存储方案':<25} | {'单例硬盘占用':<15} | {'1497例总容量预估'}")
    print("-" * 75)
    print(f"{'A. 原始直接保存 (.npy)':<25} | {size_raw:^12.2f} GB | {size_raw * 1497:^12.1f} GB")
    print(f"{'B. 仅物理裁剪 (.npy)':<25} | {size_crop:^12.2f} GB | {size_crop * 1497:^12.1f} GB")
    print(f"{'C. 裁剪 + HDF5压缩 (.h5)':<25} | {size_h5:^12.2f} GB | {size_h5 * 1497:^12.1f} GB (⭐最终推荐)")
    print("-" * 75)
    print(f"✅ 数学无损验证结果: {'【通过】复原数据与原始真值 100% 逐像素一致' if is_perfect else '【失败】数据存在差异'}")
    print(f"⏱️ HDF5 压缩与打包耗时: {t_end - t_start:.2f} 秒")
    print("="*75)
    
    # 明确提示文件已保留
    print(f"\n📁 [全部文件已保留] 你可以在以下路径查看并进行可视化对比:")
    print(f" - 原始全量: {path_raw}")
    print(f" - 裁剪数据: {path_crop}")
    print(f" - 终极压缩: {path_h5}")

if __name__ == "__main__":
    run_ultimate_benchmark()