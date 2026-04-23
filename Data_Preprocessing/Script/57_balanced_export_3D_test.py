import os
import pydicom
import numpy as np
import h5py
import time
from scipy import ndimage
from scipy.ndimage import zoom
from skimage import measure
import trimesh
from trimesh.smoothing import filter_taubin
from collections import defaultdict
from tqdm import tqdm

# ==========================================
# 🌟 57号自主调参区 (吴刚专供)
# ==========================================
# 1. 空间缩放因子 (决定颗粒度)
# 1.0 = 原生CT精度 | 1.5 = 高清插值 | 2.0 = 超采样(极慢但极细)
ZOOM_FACTOR = 1.0  

# 2. 存储位深
# np.float32 = 满血科研精度 | np.float16 = 压缩模式
DTYPE_MODE = np.float32 

# 3. 骨骼阈值 (决定胖瘦)
# 150 = 较丰满(你之前的满意值) | 250 = 较精炼
THRESHOLD = 150  

# 4. 愈合与平滑
HEAL_ITERATIONS = 2   # 填补空洞的强度
SMOOTH_ITERATIONS = 0 # 0为原生计算模式(无坐标偏移) | 5-10为视觉展示模式

# ==========================================
# 路径配置
# ==========================================
DICOM_DIR = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CT0143767'
OUTPUT_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'
OUTPUT_H5 = os.path.join(OUTPUT_DIR, '57_Balanced_result.h5')
OUTPUT_STL = os.path.join(OUTPUT_DIR, '57_Balanced_result.stl')

def extract_bone_core(data, threshold, heal_iter):
    binary_mask = data > threshold
    if heal_iter > 0:
        binary_mask = ndimage.binary_closing(binary_mask, iterations=heal_iter)
        binary_mask = ndimage.binary_fill_holes(binary_mask)
        
    labeled_array, num_features = ndimage.label(binary_mask)
    if num_features == 0: return None, None, None
    
    sizes = np.bincount(labeled_array.ravel())
    sizes[0] = 0 
    largest_label = sizes.argmax()
    cleaned_mask = (labeled_array == largest_label)
    
    coords = np.argwhere(cleaned_mask)
    min_idx, max_idx = coords.min(axis=0), coords.max(axis=0)
    min_idx = np.maximum(min_idx - 10, 0)
    max_idx = np.minimum(max_idx + 10, np.array(data.shape) - 1)
    
    return min_idx, max_idx, cleaned_mask

def run_pipeline():
    print(f"🚀 [57号: 满血版] 启动！精度设定: {DTYPE_MODE.__name__} | 缩放: {ZOOM_FACTOR}x")
    t_start = time.time()

    # --- 1. 读取与坐标校准 ---
    series_dict = defaultdict(list)
    for f in os.listdir(DICOM_DIR):
        if f.endswith('.dcm'):
            filepath = os.path.join(DICOM_DIR, f)
            ds = pydicom.dcmread(filepath, stop_before_pixels=True)
            series_dict[ds.SeriesInstanceUID].append(filepath)

    best_series_uid = max(series_dict, key=lambda k: len(series_dict[k]))
    slices = [pydicom.dcmread(f) for f in series_dict[best_series_uid]]
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    
    volume_raw = np.stack([s.pixel_array for s in slices]).astype(np.float32)
    pixel_spacing = slices[0].PixelSpacing
    z_spacing = abs(float(slices[1].ImagePositionPatient[2]) - float(slices[0].ImagePositionPatient[2]))

    # --- 2. 空间重采样 ---
    print(f"⏳ 正在执行 {ZOOM_FACTOR}x 重采样...")
    volume_resampled = zoom(volume_raw, ZOOM_FACTOR, order=1)
    spacing_final = (z_spacing / ZOOM_FACTOR, float(pixel_spacing[0]) / ZOOM_FACTOR, float(pixel_spacing[1]) / ZOOM_FACTOR)

    # --- 3. 连通域修复与裁剪 ---
    print(f"⏳ 正在执行 3D 修复 (阈值:{THRESHOLD})...")
    min_idx, max_idx, cleaned_mask = extract_bone_core(volume_resampled, THRESHOLD, HEAL_ITERATIONS)
    volume_resampled[~cleaned_mask] = 0
    
    cropped = volume_resampled[min_idx[0]:max_idx[0]+1, min_idx[1]:max_idx[1]+1, min_idx[2]:max_idx[2]+1]
    final_data = cropped.astype(DTYPE_MODE)

    # --- 4. 导出 HDF5 ---
    t0 = time.time()
    with h5py.File(OUTPUT_H5, 'w') as f:
        f.create_dataset('stress_field', data=final_data, compression="gzip", compression_opts=4)
        f.create_dataset('spacing', data=np.array(spacing_final))
    size_h5 = os.path.getsize(OUTPUT_H5) / (1024**2)
    print(f"✅ HDF5已保存: {size_h5:.2f} MB")

    # --- 5. 导出 STL ---
    print(f"⏳ 正在生成 STL (平滑次数:{SMOOTH_ITERATIONS})...")
    verts, faces, normals, values = measure.marching_cubes(final_data, level=THRESHOLD, spacing=spacing_final)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals)
    
    # 自动剔除孤岛
    components = mesh.split(only_watertight=False)
    if len(components) > 1:
        mesh = max(components, key=lambda m: len(m.faces))

    if SMOOTH_ITERATIONS > 0:
        filter_taubin(mesh, iterations=SMOOTH_ITERATIONS)
        
    mesh.export(OUTPUT_STL)
    size_stl = os.path.getsize(OUTPUT_STL) / (1024**2)
    print(f"✅ STL已保存: {size_stl:.2f} MB")

    print("\n" + "="*60)
    print(f"🏆 任务完成！总耗时: {time.time() - t_start:.2f} 秒")
    print(f"📊 最终体素尺寸 (mm): {spacing_final[0]:.3f} x {spacing_final[1]:.3f} x {spacing_final[2]:.3f}")
    print(f"📂 HDF5 大小: {size_h5:.2f} MB")
    print(f"📂 STL 大小: {size_stl:.2f} MB")
    print("="*60)

if __name__ == "__main__":
    run_pipeline()