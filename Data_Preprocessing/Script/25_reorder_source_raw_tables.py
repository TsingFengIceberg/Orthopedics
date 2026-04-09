import os
import shutil
import pandas as pd

# ================= 配置路径 =================
src_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Rename_Raw_Tables'
tgt_dir = '/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Table_Dataset/Resort_Raw_Tables'

os.makedirs(tgt_dir, exist_ok=True)

# ================= 检验表处理（直接复制） =================
lab_files = ['Lab_Results_1.xlsx', 'Lab_Results_2.xlsx', 'Lab_Results_3.xlsx']
print("🚀 开始处理检验数据表 (直接复制)...")
for file in lab_files:
    src_path = os.path.join(src_dir, file)
    tgt_path = os.path.join(tgt_dir, file)
    if os.path.exists(src_path):
        shutil.copy2(src_path, tgt_path)
        print(f"  ✅ {file} 复制完成。")
    else:
        print(f"  ⚠️ 未找到 {file}，已跳过。")

# ================= 需重排列表格的配置字典 =================
table_configs = {
    'Nursing_Assessments.xlsx': {'id_col': 'PATIENT_ID', 'time_col': 'CREATED_DATE', 'dt_format': 'yyyy/m/d h:mm:ss'},
    'Pain_Scores.xlsx': {'id_col': 'PATIENT_ID', 'time_col': 'CREATED_DATE', 'dt_format': 'yyyy/m/d h:mm:ss'},
    'Comprehensive_Clinical_Records.xlsx': {'id_col': '患者ID', 'time_col': '入院时间', 'dt_format': 'yyyy/m/d h:mm:ss'},
    'Patient_Image_Mapping.xls': {'id_col': '病历号', 'time_col': '检查时间', 'dt_format': 'yyyy-mm-dd hh:mm:ss'}
}

# ================= 开始处理并排序 =================
print("\n🚀 开始处理并重排临床及评分数据表...")

for src_file, config in table_configs.items():
    src_path = os.path.join(src_dir, src_file)
    
    # 后缀升级逻辑
    if src_file.endswith('.xls') and not src_file.endswith('.xlsx'):
        tgt_file = src_file.replace('.xls', '.xlsx')
    else:
        tgt_file = src_file
        
    tgt_path = os.path.join(tgt_dir, tgt_file)
    
    if not os.path.exists(src_path):
        print(f"  ⚠️ 未找到 {src_file}，已跳过。")
        continue
        
    print(f"\n📂 正在处理: {src_file}")
    id_col = config['id_col']
    time_col = config['time_col']
    dt_format = config['dt_format'] # 获取该表专属的时间格式
    
    # 1. 读取数据（强行把 ID 列读取为字符串）
    df = pd.read_excel(src_path, dtype={id_col: str})
    
    # 2. 处理无名索引列
    if df.columns[0].startswith('Unnamed'):
        df.rename(columns={df.columns[0]: 'Raw_Index'}, inplace=True)
        print("  -> 已将无名索引列重命名为 'Raw_Index'")
        
    # 3. 提取时间辅助列
    df['_temp_datetime'] = pd.to_datetime(df[time_col], errors='coerce')
    
    invalid_dates = df[df['_temp_datetime'].isna() & df[time_col].notna()]
    if not invalid_dates.empty:
        print(f"  ⚠️ 警告: 发现 {len(invalid_dates)} 条无法识别为时间的异常条目！")
        
    # 4. 排序逻辑
    patient_min_time = df.groupby(id_col)['_temp_datetime'].min().reset_index()
    patient_min_time.rename(columns={'_temp_datetime': '_patient_earliest_time'}, inplace=True)
    df = df.merge(patient_min_time, on=id_col, how='left')
    
    df.sort_values(by=['_patient_earliest_time', id_col, '_temp_datetime'], 
                   ascending=[True, True, True], 
                   inplace=True)
    
    # 5. 格式还原与清理辅助列
    df.drop(columns=['_temp_datetime', '_patient_earliest_time'], inplace=True)
    df[id_col] = df[id_col].astype(str)
    
    # 6. 【核心修复】使用 ExcelWriter 并强制指定 datetime_format
    # 这样所有被 Pandas 识别为日期的列（包括入院时间、出院时间等）都会乖乖按照这个格式写入
    with pd.ExcelWriter(tgt_path, engine='openpyxl', datetime_format=dt_format) as writer:
        df.to_excel(writer, index=False)
        
    print(f"  ✅ 排序完成并成功保存至: {tgt_path}")

print("\n🎉 所有任务处理完毕！")