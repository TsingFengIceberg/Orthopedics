import os
import pandas as pd

# ================= 配置路径 =================
temp_dir = '../Temp_data'
files_to_check = [
    '10_CT_Metadata_Clean.csv',
    '10_MR_Metadata_Clean.csv',
    '10_XRay_Metadata_Clean.csv'
]

print("🚀 [46号] 启动三大核心模态表总量极速核对引擎...\n")

total_rows = 0

print("📂 正在清点各基准表存活记录数...")

for file_name in files_to_check:
    file_path = os.path.join(temp_dir, file_name)
    
    if os.path.exists(file_path):
        try:
            # 🌟 极速魔法：只需统计行数，所以只加载第一列，避免爆内存和耗时
            df = pd.read_csv(file_path, usecols=[0], low_memory=False)
            count = len(df)
            total_rows += count
            
            # 格式化输出，对齐比较好看
            print(f"   📊 {file_name.ljust(30)} : {count:>10,} 条记录")
        except Exception as e:
            print(f"   ❌ 读取 {file_name} 失败: {e}")
    else:
        print(f"   ⚠️ 找不到文件: {file_name} (请确认 10 号脚本是否已成功生成该文件)")

print("\n" + "="*50)
print(f"🏆 终极盘点：三大纯净模态表合计共包含 {total_rows:,} 条高质量 DICOM 记录！")
print("="*50)
print("\n💡 提示：这个总数应该与你 03 号脚本提取的总文件数（去除垃圾模态后）高度一致。拿着这个底账，我们可以安心进行下一步的映射了！")