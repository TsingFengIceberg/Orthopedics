import os
import pydicom
import numpy as np
import h5py
import time
import gc
from scipy import ndimage
from scipy.ndimage import zoom
from skimage import measure
import trimesh
from trimesh.smoothing import filter_taubin
from collections import defaultdict
from tqdm import tqdm

# ==========================================
# 🌟 58号多尺度编译配置区
# ==========================================
# 1. 定义需要同时输出的缩放因子列表
ZOOM_FACTORS = [1.0, 1.25, 1.5]

# 2. 存储位深
DTYPE_MODE = np.float32 

# 3. 骨骼形态控制
THRESHOLD = 150  
HEAL_ITERATIONS = 2   
SMOOTH_ITERATIONS = 0 

# ==========================================
# 路径配置
# ==========================================
DICOM_DIR = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CT0143767'
OUTPUT_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'

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

def run_multi_scale_pipeline():
    print(f"🚀 [58号: 多尺度编译引擎] 启动！")
    print(f"🎯 目标精度列表: {ZOOM_FACTORS}x | 存储模式: {DTYPE_MODE.__name__}")
    t_total_start = time.time()

    # --- 1. 全局只执行一次：读取与坐标校准 ---
    print("\n[阶段 1] 正在执行全局 DICOM 加载与物理坐标系对齐 (仅需一次)...")
    series_dict = defaultdict(list)
    for f in tqdm(os.listdir(DICOM_DIR), desc="扫描 DICOM"):
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
    
    print(f"✅ 基准矩阵已就绪: {volume_raw.shape} | 基础物理间距: Z={z_spacing:.3f}, Y={pixel_spacing[0]:.3f}, X={pixel_spacing[1]:.3f}")

    # --- 2. 循环处理各个缩放因子 ---
    for zoom_factor in ZOOM_FACTORS:
        print("\n" + "="*60)
        print(f"🔄 正在处理缩放分支: 【 {zoom_factor}x 】")
        print("="*60)
        t_branch = time.time()

        output_h5 = os.path.join(OUTPUT_DIR, f'58_Scale_{zoom_factor}x.h5')
        output_stl = os.path.join(OUTPUT_DIR, f'58_Scale_{zoom_factor}x.stl')

        # [A] 空间重采样
        print(f"⏳ [{zoom_factor}x] 正在执行重采样计算...")
        volume_resampled = zoom(volume_raw, zoom_factor, order=1)
        spacing_final = (z_spacing / zoom_factor, float(pixel_spacing[0]) / zoom_factor, float(pixel_spacing[1]) / zoom_factor)

        # [B] 连通域修复与裁剪
        print(f"⏳ [{zoom_factor}x] 正在提取核心骨骼并修复形态...")
        min_idx, max_idx, cleaned_mask = extract_bone_core(volume_resampled, THRESHOLD, HEAL_ITERATIONS)
        
        if cleaned_mask is None:
            print(f"❌ [{zoom_factor}x] 提取失败，跳过该分支。")
            continue
            
        volume_resampled[~cleaned_mask] = 0
        cropped = volume_resampled[min_idx[0]:max_idx[0]+1, min_idx[1]:max_idx[1]+1, min_idx[2]:max_idx[2]+1]
        final_data = cropped.astype(DTYPE_MODE)

        # [C] 导出 HDF5
        print(f"⏳ [{zoom_factor}x] 正在导出底层数据保险箱 (HDF5)...")
        with h5py.File(output_h5, 'w') as f:
            f.create_dataset('stress_field', data=final_data, compression="gzip", compression_opts=4)
            f.create_dataset('spacing', data=np.array(spacing_final))
        size_h5 = os.path.getsize(output_h5) / (1024**2)

        # [D] 导出 STL
        print(f"⏳ [{zoom_factor}x] 正在渲染并导出三维网格模型 (STL)...")
        verts, faces, normals, values = measure.marching_cubes(final_data, level=THRESHOLD, spacing=spacing_final)
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals)
        
        components = mesh.split(only_watertight=False)
        if len(components) > 1:
            mesh = max(components, key=lambda m: len(m.faces))

        if SMOOTH_ITERATIONS > 0:
            filter_taubin(mesh, iterations=SMOOTH_ITERATIONS)
            
        mesh.export(output_stl)
        size_stl = os.path.getsize(output_stl) / (1024**2)

        print(f"✅ 【 {zoom_factor}x 】分支完成！耗时: {time.time() - t_branch:.2f} 秒")
        print(f"   📂 H5大小: {size_h5:.2f} MB | STL大小: {size_stl:.2f} MB")
        print(f"   📏 最终体素: {spacing_final[0]:.3f} x {spacing_final[1]:.3f} x {spacing_final[2]:.3f} mm")

        # 🧹 核心：清理该分支产生的庞大中间变量，释放内存给下一个精度使用
        del volume_resampled, cleaned_mask, cropped, final_data, mesh
        gc.collect()

    print("\n" + "🌟"*30)
    print(f"🎉 58号：所有尺度编译圆满结束！总耗时: {time.time() - t_total_start:.2f} 秒")
    print("🌟"*30)

if __name__ == "__main__":
    run_multi_scale_pipeline()