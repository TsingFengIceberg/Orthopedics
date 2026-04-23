import os
import pydicom
import numpy as np
import h5py
import time
from scipy.ndimage import zoom, label
from skimage import measure
import trimesh
from collections import defaultdict
from tqdm import tqdm

# ==========================================
# 1. 全局测试配置 (🌟 极限速度模式)
# ==========================================
DICOM_DIR = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CT0143767'
OUTPUT_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'
OUTPUT_H5 = os.path.join(OUTPUT_DIR, '56_Fast_Storage_fp16.h5')
OUTPUT_STL = os.path.join(OUTPUT_DIR, '56_Fast_Preview.stl')

# 测试期最低分辨率：降采样到 0.5x (体积变为 1/8，速度极快)
ZOOM_FACTOR = 0.5  
THRESHOLD = 250

def get_bounding_box(data, threshold=250):
    binary_mask = data > threshold
    labeled_array, num_features = label(binary_mask)
    if num_features == 0: return None
    sizes = np.bincount(labeled_array.ravel())
    sizes[0] = 0 
    largest_label = sizes.argmax()
    cleaned_mask = (labeled_array == largest_label)
    coords = np.argwhere(cleaned_mask)
    min_idx, max_idx = coords.min(axis=0), coords.max(axis=0)
    # 留点安全边距
    min_idx = np.maximum(min_idx - 10, 0)
    max_idx = np.minimum(max_idx + 10, np.array(data.shape) - 1)
    return min_idx, max_idx

def run_fast_pipeline():
    print(f"🚀 [56号: 极速双轨引擎] 启动！当前缩放比例: {ZOOM_FACTOR}x")
    t_start_total = time.time()

    # --- A. 智能读取与绝对坐标系校准 ---
    print("\n[1/5] 正在解析 DICOM 黄金元数据 (防止错位/断层)...")
    series_dict = defaultdict(list)
    files = [f for f in os.listdir(DICOM_DIR) if f.endswith('.dcm')]
    
    for f in tqdm(files, desc="扫描序列"):
        filepath = os.path.join(DICOM_DIR, f)
        ds = pydicom.dcmread(filepath, stop_before_pixels=True)
        series_dict[ds.SeriesInstanceUID].append(filepath)

    best_series_uid = max(series_dict, key=lambda k: len(series_dict[k]))
    best_files = series_dict[best_series_uid]
    
    slices = [pydicom.dcmread(f) for f in best_files]
    # 🌟 核心修复：根据 ImagePositionPatient[2] (绝对 Z 坐标) 排序
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    
    volume_raw = np.stack([s.pixel_array for s in slices]).astype(np.float32)
    original_shape = volume_raw.shape
    
    # 获取真实物理间距
    pixel_spacing = slices[0].PixelSpacing
    z_spacing = abs(float(slices[1].ImagePositionPatient[2]) - float(slices[0].ImagePositionPatient[2]))
    print(f"✅ 提取真实物理间距 (Z, Y, X): {z_spacing:.3f}, {pixel_spacing[0]:.3f}, {pixel_spacing[1]:.3f} mm")

    # --- B. 极速降维降采样 ---
    print(f"\n[2/5] 正在执行 {ZOOM_FACTOR}x 降采样 (释放内存极限加速)...")
    t0 = time.time()
    volume_small = zoom(volume_raw, ZOOM_FACTOR, order=1)
    # 同步调整物理间距 (分辨率降低，间距变大)
    spacing_small = (z_spacing / ZOOM_FACTOR, float(pixel_spacing[0]) / ZOOM_FACTOR, float(pixel_spacing[1]) / ZOOM_FACTOR)
    print(f"✅ 降维完成，耗时 {time.time()-t0:.2f}s | 新尺寸: {volume_small.shape}")

    # --- C. 核心骨骼提取 ---
    print("\n[3/5] 正在裁剪核心 Bounding Box...")
    bbox = get_bounding_box(volume_small, threshold=THRESHOLD)
    min_idx, max_idx = bbox
    cropped_volume = volume_small[min_idx[0]:max_idx[0]+1, min_idx[1]:max_idx[1]+1, min_idx[2]:max_idx[2]+1]
    
    # 转换为终极半精度
    cropped_fp16 = cropped_volume.astype(np.float16)
    print(f"✅ 裁剪完成 | 核心区域尺寸: {cropped_fp16.shape}")

    # --- D. 导出任务 1：HDF5 终极压缩包 ---
    print("\n[4/5] 正在封装 FP16 .h5 压缩舱...")
    t0 = time.time()
    with h5py.File(OUTPUT_H5, 'w') as f:
        f.create_dataset('stress_field', data=cropped_fp16, compression="gzip", compression_opts=4)
        f.create_dataset('bbox_min', data=min_idx)
        f.create_dataset('bbox_max', data=max_idx)
        f.create_dataset('original_shape', data=np.array(volume_small.shape))
    size_h5 = os.path.getsize(OUTPUT_H5) / (1024 * 1024)
    print(f"✅ HDF5 保存成功，耗时 {time.time()-t0:.2f}s")

    # --- E. 导出任务 2：STL 傻瓜 3D 模型 ---
    print("\n[5/5] 正在渲染并导出 STL 3D 模型...")
    t0 = time.time()
    # 传入真实的 spacing_small，彻底解决“压扁”问题！
    verts, faces, normals, values = measure.marching_cubes(cropped_fp16, level=THRESHOLD, spacing=spacing_small)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals)
    mesh.export(OUTPUT_STL)
    size_stl = os.path.getsize(OUTPUT_STL) / (1024 * 1024)
    print(f"✅ STL 生成成功，耗时 {time.time()-t0:.2f}s")

    print("\n" + "="*70)
    print(f"🏆 56号：全流程跑通！总耗时: {time.time() - t_start_total:.2f} 秒")
    print("="*70)
    print(f"📦 【底层数据】 HDF5 压缩包: {size_h5:.2f} MB  (极其轻量！)")
    print(f"   📂 路径: {OUTPUT_H5}")
    print("-" * 70)
    print(f"🦴 【可视化】   STL 傻瓜模型: {size_stl:.2f} MB")
    print(f"   📂 路径: {OUTPUT_STL}")
    print("="*70)
    print("👉 下一步：把生成的 .stl 文件下载到本地，双击用 Windows 查看。")
    print("   你将看到一个【不断层】、【比例完全真实 (不扁)】的完美 3D 脊柱！")

if __name__ == "__main__":
    run_fast_pipeline()