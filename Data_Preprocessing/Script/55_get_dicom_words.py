import pandas as pd
import os

# ==========================================
# 1. 路径配置
# ==========================================
INPUT_CSV = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data/10_CT_Metadata_Clean.csv'
OUTPUT_CSV = '/home/wugang/Data/Projects/Orthopedics/Data_Preprocessing/Temp_data/55_dicom_words.csv'

def extract_dicom_columns():
    print("🚀 [55号: DICOM字段提取器] 启动！")
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ 找不到输入文件: {INPUT_CSV}")
        return

    # --- A. 高效读取表头 ---
    # nrows=0 表示只读取列名，不加载任何实际数据行，瞬间完成
    df_head = pd.read_csv(INPUT_CSV, nrows=0)
    
    # --- B. 转换为竖向表格 ---
    # 将提取到的列名列表（横向）转换为 DataFrame（竖向）
    columns_df = pd.DataFrame({
        'DICOM_Keywords': df_head.columns
    })
    
    # --- C. 保存为新 CSV ---
    columns_df.to_csv(OUTPUT_CSV, index=False)
    
    print("\n" + "="*60)
    print("🎉 字段提取成功！")
    print("="*60)
    print(f"✅ 共提取字段数: {len(df_head.columns)} 个")
    print(f"📁 导出路径: {OUTPUT_CSV}")
    print("="*60)

if __name__ == "__main__":
    extract_dicom_columns()