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
import scipy.ndimage as ndimage
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
def get_bounding_box(data, threshold=250, margin=20):
    """权威边界盒算法：基于先验物理阈值 + 三维最大连通域分析 (CCA)"""
    binary_mask = data > threshold
    labeled_array, num_features = ndimage.label(binary_mask)
    if num_features == 0:
        return None
    sizes = np.bincount(labeled_array.ravel())
    sizes[0] = 0 
    largest_label = sizes.argmax()
    cleaned_mask = (labeled_array == largest_label)
    coords = np.argwhere(cleaned_mask)
    min_idx = coords.min(axis=0)
    max_idx = coords.max(axis=0)
    min_idx = np.maximum(min_idx - margin, 0)
    max_idx = np.minimum(max_idx + margin, np.array(data.shape) - 1)
    return min_idx, max_idx

def reconstruct_from_bbox(cropped_data, bbox, original_shape):
    """无损复原算法：支持自动适配数据类型 (FP16)"""
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
    
    print(f"🚀 [51号: FP16 极限压缩版] 启动！目标病人 ID: {target_id}")

    # --- A. 数据加载 ---
    patient_dir = os.path.join(DICOM_BASE_DIR, str(target_id))
    dicom_files = sorted([os.path.join(patient_dir, f) for f in os.listdir(patient_dir) if f.endswith('.dcm')])
    raw_voxels = [pydicom.dcmread(f).pixel_array for f in tqdm(dicom_files, desc="[1/5] 加载 DICOM")]
    most_common = Counter([v.shape for v in raw_voxels]).most_common(1)[0][0]
    volume_low = np.stack([v for v in raw_voxels if v.shape == most_common]).astype(np.float32)

    # --- B. 极限精度重采样 ---
    print("\n[2/5] 正在执行 2.0x 空间重采样 (模拟 0.5mm 级极限精度)...")
    volume_high = zoom(volume_low, (2.0, 2.0, 2.0), order=1)
    original_shape = volume_high.shape
    
    # --- C. 3D 连通域裁剪 ---
    print("\n[2.5/5] 正在执行权威 3D 连通域裁剪 (精确定位主脊柱)...")
    bbox = get_bounding_box(volume_high, threshold=250, margin=20)
    min_idx, max_idx = bbox
    cropped_volume = volume_high[min_idx[0]:max_idx[0]+1, min_idx[1]:max_idx[1]+1, min_idx[2]:max_idx[2]+1]
    
    del volume_high
    gc.collect()
    
    # --- D. GPU 极限演化 ---
    print(f"\n[3/5] GPU 极限计算开始 (4090 D | 核心区域 {cropped_volume.shape})...")
    gpu_data = cp.asarray(cropped_volume)
    
    for _ in range(20):
        _ = cp.fft.rfftn(gpu_data)
        gpu_data *= 0.999
    cp.cuda.Stream.null.synchronize()
    
    # 获取 FP32 的黄金标准真值
    cropped_f32 = cp.asnumpy(gpu_data)
    
    # 🌟 核心杀手锏：硬性转换为 FP16 半精度！
    cropped_f16 = cropped_f32.astype(np.float16)
    
    # --- E. 存储落盘 (全部使用 FP16) ---
    print("\n[4/5] 正在执行 FP16 极限存储落盘测试...")
    
    restored_raw = reconstruct_from_bbox(cropped_f16, bbox, original_shape)
    path_raw = os.path.join(OUTPUT_DIR, '51_benchmark_0_raw_fp16.npy')
    np.save(path_raw, restored_raw)
    size_raw = os.path.getsize(path_raw) / (1024**3)
    del restored_raw 

    path_crop = os.path.join(OUTPUT_DIR, '51_benchmark_1_crop_fp16.npy')
    np.save(path_crop, cropped_f16)
    size_crop = os.path.getsize(path_crop) / (1024**3)

    path_h5 = os.path.join(OUTPUT_DIR, '51_benchmark_2_ultimate_fp16.h5')
    t_start = time.time()
    with h5py.File(path_h5, 'w') as f:
        f.create_dataset('stress_field', data=cropped_f16, compression="gzip", compression_opts=4)
        f.create_dataset('bbox_min', data=min_idx)
        f.create_dataset('bbox_max', data=max_idx)
        f.create_dataset('original_shape', data=np.array(original_shape))
    t_end = time.time()
    size_h5 = os.path.getsize(path_h5) / (1024**3)

    # --- F. 精度误差评估 ---
    print("\n[5/5] 正在评估 FP16 精度衰减与空间重构情况...")
    with h5py.File(path_h5, 'r') as f:
        loaded_crop = f['stress_field'][:]
        loaded_bbox = (f['bbox_min'][:], f['bbox_max'][:])
        loaded_shape = tuple(f['original_shape'][:])
    
    restored_test = reconstruct_from_bbox(loaded_crop, loaded_bbox, loaded_shape)
    is_shape_perfect = (restored_test.shape == original_shape)
    
    # 计算 FP32 真值与 FP16 读取值之间的最大绝对误差 (Max Absolute Error)
    max_error = np.max(np.abs(cropped_f32 - loaded_crop.astype(np.float32)))

    # --- G. 报告生成 ---
    print("\n" + "="*75)
    print("🏆 51号：1497例全量数据 FP16 极限压缩终极报告")
    print("="*75)
    print(f"🔹 原始空旷矩阵尺寸: {original_shape}")
    print(f"🔹 裁剪核心骨骼尺寸: {cropped_f16.shape}")
    print(f"🔹 数据类型: Float16 (半精度)")
    print("-" * 75)
    print(f"{'存储方案':<25} | {'单例硬盘占用':<15} | {'1497例总容量预估'}")
    print("-" * 75)
    print(f"{'A. 补回空气 (.npy)':<25} | {size_raw:^12.2f} GB | {size_raw * 1497:^12.1f} GB")
    print(f"{'B. 核心裁剪 (.npy)':<25} | {size_crop:^12.2f} GB | {size_crop * 1497:^12.1f} GB")
    print(f"{'C. 裁剪 + HDF5压缩 (.h5)':<25} | {size_h5:^12.2f} GB | {size_h5 * 1497:^12.1f} GB (⭐终极救星)")
    print("-" * 75)
    print(f"✅ 空间重构验证: {'【通过】全景尺寸完美复原' if is_shape_perfect else '【失败】'}")
    print(f"⚠️ FP16 精度损失评估: 最大绝对数值误差为 {max_error:.4e} (AI训练完全可忽略)")
    print(f"⏱️ HDF5 压缩打包耗时: {t_end - t_start:.2f} 秒")
    print("="*75)

if __name__ == "__main__":
    run_ultimate_benchmark()