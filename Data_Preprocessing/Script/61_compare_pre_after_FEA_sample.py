import os
import glob
import time
import h5py
import numpy as np
import cupy as cp
import pydicom
from scipy import ndimage
from skimage import measure
import trimesh
import pyvista as pv

# ==========================================
# 🌟 61号：纵向黄金病例 FEA 全链路生成器 (防爆读取 + C序防闪退输出)
# ==========================================

# --- 参数配置区 ---
ZOOM_FACTOR = 1.25
DTYPE_MODE = np.float32
THRESHOLD = 150
HEAL_ITERATIONS = 2
EXPONENT = 1.8

# --- 路径配置区 ---
DICOM_BASE_DIR = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS'
# 直接输出到 Temp_data，不建子文件夹
OUTPUT_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'

# 目标测试病例
TARGET_FOLDERS = [
    {'id': 'Time1_Pre_Fracture', 'folder': 'RK_NCT202404110319'},
    {'id': 'Time2_Post_Fracture', 'folder': 'CT0150149'}
]

def load_dicom_volume(folder_path):
    """读取并重建 3D DICOM 矩阵（保留智能过滤定位片防爆机制）"""
    files = glob.glob(os.path.join(folder_path, '*.dcm'))
    if not files:
        raise ValueError(f"文件夹为空或无DCM文件: {folder_path}")
        
    # 1. 尝试读取所有文件
    raw_slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(f, force=True)
            if hasattr(ds, 'pixel_array'):
                raw_slices.append(ds)
        except Exception:
            continue

    if not raw_slices:
        raise ValueError(f"未能从 {folder_path} 解析出任何带像素的 DICOM 文件")

    # 2. 核心防爆：按 SeriesInstanceUID 分组，过滤掉多余的定位片或重建图
    series_dict = {}
    for s in raw_slices:
        uid = s.SeriesInstanceUID if hasattr(s, 'SeriesInstanceUID') else 'unknown'
        if uid not in series_dict:
            series_dict[uid] = []
        series_dict[uid].append(s)

    # 自动挑选切片数量最多的那个序列（主 CT 序列）
    largest_series = max(series_dict.values(), key=len)

    # 3. 终极防爆盾：确保挑选出的序列中，所有二维矩阵的 shape 绝对一致
    from collections import Counter
    shapes = [s.pixel_array.shape for s in largest_series]
    most_common_shape = Counter(shapes).most_common(1)[0][0]
    valid_slices = [s for s in largest_series if s.pixel_array.shape == most_common_shape]

    # 4. 物理 Z 轴排序
    valid_slices.sort(key=lambda x: float(x.ImagePositionPatient[2]) if hasattr(x, 'ImagePositionPatient') else x.InstanceNumber)
    
    # 5. 提取物理间距 [Z, Y, X]
    if len(valid_slices) > 1 and hasattr(valid_slices[0], 'ImagePositionPatient') and hasattr(valid_slices[1], 'ImagePositionPatient'):
        z_spacing = float(abs(valid_slices[0].ImagePositionPatient[2] - valid_slices[1].ImagePositionPatient[2]))
    else:
        z_spacing = float(valid_slices[0].SliceThickness) if hasattr(valid_slices[0], 'SliceThickness') else 1.0
        
    y_spacing, x_spacing = map(float, valid_slices[0].PixelSpacing)
    original_spacing = np.array([z_spacing, y_spacing, x_spacing])
    
    # 6. 转换为 HU 值
    image_volume = np.stack([s.pixel_array for s in valid_slices]).astype(DTYPE_MODE)
    intercept = float(valid_slices[0].RescaleIntercept) if hasattr(valid_slices[0], 'RescaleIntercept') else 0.0
    slope = float(valid_slices[0].RescaleSlope) if hasattr(valid_slices[0], 'RescaleSlope') else 1.0
    hu_volume = image_volume * slope + intercept
    
    print(f"   [过滤日志] 总文件数:{len(files)} -> 过滤后有效切片数:{len(valid_slices)}")
    
    return hu_volume, original_spacing

def process_single_case(case_info):
    time_id = case_info['id']
    folder_name = case_info['folder']
    dicom_path = os.path.join(DICOM_BASE_DIR, folder_name)
    
    print(f"\n" + "="*55)
    print(f"🚀 开始处理纵向切面: 【{time_id}】")
    print(f"📂 数据来源: {folder_name}")
    print("="*55)
    
    total_start = time.time()
    
    # ---------------------------------------------------------
    # Step 1: 读取与重采样
    # ---------------------------------------------------------
    t0 = time.time()
    print(f"📥 [1/4] 读取 DICOM 并执行 {ZOOM_FACTOR}x 重采样...")
    hu_volume, orig_spacing = load_dicom_volume(dicom_path)
    
    hu_volume = ndimage.zoom(hu_volume, ZOOM_FACTOR, order=1)
    new_spacing = orig_spacing / ZOOM_FACTOR
    print(f"   - 矩阵形状: {hu_volume.shape}, 物理间距: {new_spacing}")
    print(f"   - 耗时: {time.time()-t0:.2f}s")
    
    # ---------------------------------------------------------
    # Step 2: 骨芯提取
    # ---------------------------------------------------------
    t0 = time.time()
    print(f"🦴 [2/4] 形态学提取骨芯 (HU > {THRESHOLD})...")
    binary_mask = hu_volume > THRESHOLD
    binary_mask = ndimage.binary_closing(binary_mask, iterations=HEAL_ITERATIONS)
    binary_mask = ndimage.binary_fill_holes(binary_mask)
    
    labeled_array, num_features = ndimage.label(binary_mask)
    if num_features > 0:
        sizes = ndimage.sum(binary_mask, labeled_array, range(1, num_features + 1))
        max_label = np.argmax(sizes) + 1
        binary_mask = (labeled_array == max_label)
        
    core_hu_volume = np.where(binary_mask, hu_volume, -1000).astype(DTYPE_MODE)
    print(f"   - 耗时: {time.time()-t0:.2f}s")
    
    # ---------------------------------------------------------
    # Step 3: GPU 物理映射
    # ---------------------------------------------------------
    t0 = time.time()
    print(f"⚡ [3/4] CuPy GPU 轴向应力推演...")
    gpu_data = cp.asarray(core_hu_volume, dtype=cp.float32)
    gpu_data = cp.clip(gpu_data, 0, None) 
    
    max_val = cp.max(gpu_data) + 1e-6
    e_field = cp.power(gpu_data / max_val, EXPONENT)
    
    layer_stiffness = cp.sum(e_field, axis=(1, 2), keepdims=True)
    voxel_area = new_spacing[1] * new_spacing[2]
    force_total = cp.sum(gpu_data) * voxel_area * 0.01 
    
    stress_field_gpu = (e_field / (layer_stiffness + 1e-6)) * force_total
    stress_field = cp.asnumpy(stress_field_gpu).astype(DTYPE_MODE)
    stress_field = np.where(binary_mask, stress_field, 0.0)
    
    print(f"   - 最大应力: {np.max(stress_field):.4f} MPa")
    print(f"   - 耗时: {time.time()-t0:.2f}s")
    
    # ---------------------------------------------------------
    # Step 4: 结果输出 (H5, STL, VTK, VTI)
    # ---------------------------------------------------------
    t0 = time.time()
    print(f"💾 [4/4] 正在导出成果物...")
    
    base_name = os.path.join(OUTPUT_DIR, f"61_{time_id}_{ZOOM_FACTOR}x")
    out_h5 = base_name + ".h5"
    out_stl = base_name + ".stl"
    out_vtk = base_name + ".vtk"
    out_vti = base_name + ".vti"
    
    # [A] H5
    with h5py.File(out_h5, 'w') as f:
        f.create_dataset('stress_field', data=stress_field, compression="gzip", compression_opts=4)
        f.create_dataset('spacing', data=new_spacing)
    
    # [B] STL
    verts, faces, normals, values = measure.marching_cubes(core_hu_volume, level=THRESHOLD, spacing=new_spacing)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals)
    mesh.export(out_stl)
    
    # [C] VTK & VTI (核心修复：使用 order='C' 彻底解决大数据量下的内存错位与闪退)
    z_dim, y_dim, x_dim = stress_field.shape
    grid = pv.ImageData()
    grid.dimensions = (x_dim, y_dim, z_dim)
    grid.spacing = (new_spacing[2], new_spacing[1], new_spacing[0])
    
    grid.point_data["Stress_MPa"] = stress_field.flatten(order='C')
    
    grid.save(out_vtk)
    grid.save(out_vti)
    
    print(f"   - 导出耗时: {time.time()-t0:.2f}s")
    
    # --- 日志报告 ---
    print(f"✅ 处理完成！")
    print(f"   [H5 ] {os.path.getsize(out_h5) / 1024**2:.2f} MB")
    print(f"   [STL] {os.path.getsize(out_stl) / 1024**2:.2f} MB")
    print(f"   [VTK] {os.path.getsize(out_vtk) / 1024**2:.2f} MB")
    print(f"   [VTI] {os.path.getsize(out_vti) / 1024**2:.2f} MB")

if __name__ == '__main__':
    for case in TARGET_FOLDERS:
        try:
            process_single_case(case)
        except Exception as e:
            print(f"❌ 失败: {str(e)}")