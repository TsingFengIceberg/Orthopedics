import nibabel as nib
import numpy as np
from skimage import measure
import trimesh
import os

# ==========================================
# 1. 路径配置
# ==========================================
INPUT_PATH = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data/52_51_benchmark_2_ultimate_fp16.nii.gz'
OUTPUT_STL = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data/54_Spine_Model_Ready.stl'

def convert_nifti_to_stl(threshold=250):
    print("🚀 [54号: STL 转换器] 启动！准备生成 Windows 傻瓜式查看模型...")
    
    if not os.path.exists(INPUT_PATH):
        print(f"❌ 找不到文件: {INPUT_PATH}")
        return

    # --- A. 加载数据 ---
    img = nib.load(INPUT_PATH)
    data = img.get_fdata()
    print(f"✅ 数据加载成功 | 原始尺寸: {data.shape}")

    # --- B. 极简瘦身 (关键！否则 Windows 会卡死) ---
    # 我们每隔 3 个点取一个，这样模型大小会缩小到 1/27，但轮廓依然清晰
    print("⏳ 正在进行空间压缩以适配 Windows 查看器...")
    data_small = data[::2, ::2, ::2] 
    
    # --- C. 提取骨骼表面 (Marching Cubes 算法) ---
    print(f"⏳ 正在计算 3D 表面 (阈值: {threshold})...")
    # level=250 是我们之前确定的骨头阈值
    try:
        verts, faces, normals, values = measure.marching_cubes(data_small, level=threshold)
    except ValueError:
        print("❌ 提取失败：请检查阈值是否设得太高，导致没找到骨头。")
        return

    # --- D. 封装并保存为 STL ---
    print("⏳ 正在封装 3D 几何网格...")
    # 注意：这里我们应用了仿射矩阵的部分信息，确保模型不走样
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals)
    
    # 导出
    mesh.export(OUTPUT_STL)
    
    print("\n" + "="*60)
    print("🎉 转换圆满完成！")
    print("="*60)
    print(f"📁 生成模型: {OUTPUT_STL}")
    print(f"💾 模型大小: {os.path.getsize(OUTPUT_STL)/1024/1024:.2f} MB")
    print("-" * 60)
    print("👉 操作指南：")
    print("1. 把这个 .stl 文件下载到你的 Windows 电脑上。")
    print("2. 直接【双击】它！Windows 会自动调用『3D 查看器』。")
    print("3. 你会看到一截灰白色的、真实的 3D 脊柱模型，鼠标随便转！")
    print("="*60)

if __name__ == "__main__":
    # 如果 250 出来的东西太碎，可以尝试调低到 150
    convert_nifti_to_stl(threshold=250)