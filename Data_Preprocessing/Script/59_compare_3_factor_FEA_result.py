import os
import h5py
import numpy as np
import cupy as cp
import pyvista as pv
import time

# ==========================================
# 🌟 59号：物理应力映射 (Bug 修复版)
# ==========================================
SCALES = [1.0, 1.25, 1.5]
BASE_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'

def run_physical_fea_gpu(volume_data, spacing):
    print(f"    ⚙️ [GPU 计算] 执行物理映射...")
    t_gpu_start = time.time()
    
    # 1. 搬运到 GPU
    gpu_data = cp.asarray(volume_data, dtype=cp.float32)
    
    # 🌟 关键修复：将所有负值（空气/背景）强制归零
    # 这样可以避免 power(负数, 1.8) 产生 NaN
    gpu_data = cp.clip(gpu_data, 0, None)
    
    # 2. 计算杨氏模量场
    max_val = cp.max(gpu_data) + 1e-6
    e_field = cp.power(gpu_data / max_val, 1.8)
    
    # 3. 计算轴向应力
    layer_stiffness = cp.sum(e_field, axis=(1, 2), keepdims=True)
    voxel_area = spacing[1] * spacing[2]
    
    # 避免除以 0
    stress_field = (e_field / (layer_stiffness + 1e-9)) * (500.0 / voxel_area)
    
    cp.cuda.Stream.null.synchronize()
    result = cp.asnumpy(stress_field)
    
    # 检查结果是否包含无效值
    if np.isnan(result).any():
        print("    ⚠️ 警告：检测到计算结果包含 NaN，已强制转为 0。")
        result = np.nan_to_num(result)
        
    return result

def export_to_vtk_and_png(stress_data, spacing, scale, output_png):
    print(f"    🎨 [3D 渲染] 构建 {scale}x 网格...")
    
    grid = pv.ImageData()
    grid.dimensions = (stress_data.shape[2], stress_data.shape[1], stress_data.shape[0])
    grid.spacing = (spacing[2], spacing[1], spacing[0])
    grid.point_data["Stress_MPa"] = stress_data.flatten()

    # 保存 VTK
    vtk_path = output_png.replace('.png', '.vtk')
    grid.save(vtk_path)

    # 渲染预览图
    plotter = pv.Plotter(off_screen=True)
    
    # 🌟 鲁棒性改进：如果最大值太小，使用极低阈值
    max_s = np.max(stress_data)
    threshold_val = max_s * 0.05 if max_s > 0 else 0.001
    
    bone_mesh = grid.threshold(threshold_val, scalars="Stress_MPa")
    
    # 🌟 关键修复：检查阈值后是否还有点，防止 add_mesh 报错
    if bone_mesh.n_points == 0:
        print(f"    ⚠️ 警告：{scale}x 尺度下阈值过滤后无剩余点，跳过 PNG 截图。")
        # 如果是空的，我们可以尝试渲染原始网格以供调试
        plotter.add_mesh(grid, scalars="Stress_MPa", cmap="turbo", opacity=0.5)
    else:
        plotter.add_mesh(bone_mesh, scalars="Stress_MPa", cmap="turbo", opacity=0.9)
    
    plotter.camera_position = 'iso'
    plotter.set_background("white")
    plotter.screenshot(output_png, window_size=[1920, 1080])
    plotter.close()

def main():
    print("🚀 [59号: 物理优化版 V4] 启动！")
    for scale in SCALES:
        h5_path = os.path.join(BASE_DIR, f'58_Scale_{scale}x.h5')
        out_png = os.path.join(BASE_DIR, f'59_FEA_Result_Scale_{scale}x.png')
        if not os.path.exists(h5_path): continue
            
        print("\n" + "="*60)
        print(f"🔬 正在分析: 【 {scale}x 】")
        with h5py.File(h5_path, 'r') as f:
            volume = f['stress_field'][:]
            spacing = f['spacing'][:]
            
        stress_field = run_physical_fea_gpu(volume, spacing)
        export_to_vtk_and_png(stress_field, spacing, scale, out_png)
        print(f"🎉 【 {scale}x 】处理完毕。")

if __name__ == "__main__":
    main()