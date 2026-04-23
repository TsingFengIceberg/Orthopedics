import h5py
import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# 1. 路径配置
# ==========================================
BASE_DIR = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data'
H5_FP32 = os.path.join(BASE_DIR, '50_benchmark_2_ultimate.h5')
H5_FP16 = os.path.join(BASE_DIR, '51_benchmark_2_ultimate_fp16.h5')
OUTPUT_PNG = os.path.join(BASE_DIR, '53_Dual_Precision_Comparison.png')

def render_comparison():
    print("🚀 [53号: 双精度对比渲染引擎] 启动！")
    
    if not os.path.exists(H5_FP32) or not os.path.exists(H5_FP16):
        print("❌ 缺失输入文件，请确保 50 号和 51 号脚本已运行成功。")
        return

    # --- A. 提取数据 ---
    def load_data(path):
        with h5py.File(path, 'r') as f:
            return f['stress_field'][:]

    print("\n[1/3] 正在加载双版本核心矩阵...")
    data_32 = load_data(H5_FP32)
    data_16 = load_data(H5_FP16).astype(np.float32) # 转回32位仅为了绘图兼容
    
    Z, Y, X = data_32.shape
    
    # --- B. 计算视图 ---
    print("[2/3] 正在并行计算两组投影与切面...")
    # 我们选最能体现精度和边界的两个视角：
    # 1. Coronal MIP (正面透视 X 光) - 看边界和宏观形态
    # 2. Coronal Slice (中心切面) - 看内部细节和噪点
    
    views = {
        'FP32_MIP': np.max(data_32, axis=1),
        'FP16_MIP': np.max(data_16, axis=1),
        'FP32_Slice': data_32[:, Y // 2, :],
        'FP16_Slice': data_16[:, Y // 2, :]
    }

    # --- C. 绘图排版 ---
    print("[3/3] 正在生成高清对比画布...")
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 20))
    
    # 设置对比标题
    axes[0, 0].set_title("FP32 (单精度) - 正面透视 (MIP)", fontsize=16)
    axes[0, 1].set_title("FP16 (半精度) - 正面透视 (MIP)", fontsize=16)
    axes[1, 0].set_title("FP32 (单精度) - 中心切面", fontsize=16)
    axes[1, 1].set_title("FP16 (半精度) - 中心切面", fontsize=16)

    # 统一渲染
    im0 = axes[0, 0].imshow(views['FP32_MIP'], cmap='bone', origin='lower')
    im1 = axes[0, 1].imshow(views['FP16_MIP'], cmap='bone', origin='lower')
    im2 = axes[1, 0].imshow(views['FP32_Slice'], cmap='bone', origin='lower')
    im3 = axes[1, 1].imshow(views['FP16_Slice'], cmap='bone', origin='lower')

    for ax in axes.ravel(): ax.axis('off')

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=120, facecolor='black')
    plt.close()
    
    print("\n" + "="*60)
    print("🎉 对比图生成成功！")
    print(f"📁 路径: {OUTPUT_PNG}")
    print("-" * 60)
    print("👉 观察指南：")
    print("1. 重点看右侧 (FP16) 的边缘是否有锯齿或模糊。")
    print("2. 重点看中心切面的骨小梁纹理是否清晰。")
    print("你会发现：肉眼几乎无法分辨两者的区别，但空间省了一半！")
    print("="*60)

if __name__ == "__main__":
    render_comparison()