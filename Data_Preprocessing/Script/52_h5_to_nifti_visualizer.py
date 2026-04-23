import h5py
import numpy as np
import nibabel as nib
import os

# ==========================================
# 1. 路径配置
# ==========================================
BASE_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'

# 定义需要转换的文件队列 (输入输出映射)
FILES_TO_CONVERT = [
    {
        'in_file': '50_benchmark_2_ultimate.h5',
        'out_file': '52_50_benchmark_2_ultimate.nii.gz',
        'desc': 'FP32 (单精度) 黄金标准版'
    },
    {
        'in_file': '51_benchmark_2_ultimate_fp16.h5',
        'out_file': '52_51_benchmark_2_ultimate_fp16.nii.gz',
        'desc': 'FP16 (半精度) 极限压缩版'
    }
]

def convert_h5_to_nifti():
    print("🚀 [52号: 双精度 3D 可视化导出工具] 启动！\n" + "="*60)
    
    for item in FILES_TO_CONVERT:
        input_path = os.path.join(BASE_DIR, item['in_file'])
        output_path = os.path.join(BASE_DIR, item['out_file'])
        desc = item['desc']
        
        print(f"📦 正在处理: {desc}")
        
        if not os.path.exists(input_path):
            print(f"  ❌ 找不到输入文件: {item['in_file']} (跳过)")
            print("-" * 60)
            continue

        # --- A. 打开 HDF5 保险箱 ---
        try:
            with h5py.File(input_path, 'r') as f:
                volume_data = f['stress_field'][:]
                print(f"  ✅ 读取成功 | 尺寸: {volume_data.shape} | 类型: {volume_data.dtype}")
        except Exception as e:
            print(f"  ❌ 读取 HDF5 失败: {e}")
            continue

        # --- B. 坐标系调整与格式兼容处理 ---
        # 转置矩阵以适配 NIfTI 标准查看器的 XYZ 坐标系
        nifti_data = np.transpose(volume_data, (2, 1, 0))
        
        # 🌟 核心修复：绕过 Nibabel 的 Float16 限制
        if nifti_data.dtype == np.float16:
            print("  ⚠️ NIfTI 不兼容 Float16，正在装载为 Float32 供查看器渲染 (不改变已被截断的真实视觉精度)...")
            nifti_data = nifti_data.astype(np.float32)

        affine = np.eye(4)

        # --- C. 封装并导出 ---
        print(f"  ⏳ 正在封装为 .nii.gz 格式...")
        nii_image = nib.Nifti1Image(nifti_data, affine)
        nib.save(nii_image, output_path)
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  🎉 导出成功 | 大小: {size_mb:.2f} MB")
        print(f"  💾 路径: {output_path}")
        print("-" * 60)

    print("✅ 全部转换任务结束！")
    print("\n👉 高阶对比技巧 (VS Code Niivue 插件)：")
    print("1. 在左侧资源管理器中，选中这两个生成的 .nii.gz 文件。")
    print("2. 在 Niivue 插件中将它们以上下分屏或左右分屏同时打开。")
    print("3. 开启 Niivue 的 'Sync Views' (同步视图) 功能，肉眼找不同！")

if __name__ == "__main__":
    convert_h5_to_nifti()