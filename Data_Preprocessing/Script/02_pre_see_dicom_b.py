import pydicom
import os
import pandas as pd

# 提供的测试文件列表（共 22 个文件，恰好 11 对）
file_paths = [
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/8126/DX_1.2.840.113564.1921830210.20250721142241647380.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/8952/DX_1.2.840.113564.1921830210.20250726154702146440.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CR0000894/DX_1.2.840.113564.1921830210.20250101084002490170.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CR0008171/DX_1.2.840.113564.1921830210.20250220093038160800.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CT0069382/CT_1.2.156.14702.1.1015.124.2.202505210934563479119.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/CT0189918/CT_1.2.156.112605.189250941543027.251220003538.4.24392.19343.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/DX  0011780/DX_1.2.840.113564.1921830210.20250813084409710400.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/DX  0011898/DX_1.2.840.113564.1921830210.20250813162910379360.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/DX0012159/DX_1.2.840.113564.1921830210.202508150821364098.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/DX0014213/DX_1.2.840.113564.1921830210.20250825153150690890.1203801020003.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/MR0016158/MR_1.2.826.0.1.3680043.10.221.6.14702.3.696.3.20250428130846005.521.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/MR0046198/MR_1.2.826.0.1.3680043.10.221.14196467.1366567.24760.1763424763.636.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_LDR202206140110/85_c5_85c5f22e-0784-4d6c-8699-b5e1538d034c.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_LDR202406110078/a4_45_a44527cf-ea02-4633-bd92-aef5db726984.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_LMR202209150025/0e_9b_0e9b1b02-562e-41b1-a174-e780c48c261b.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_LMR202103290072/3f_bd_3fbda995-7d83-4b81-b16d-049247781184.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NCT202012020158/00_88_00883c37-720f-45ec-9635-d50db118d301.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NCT202208310025/0b_3c_0b3c6aa3-9fe2-4cd9-a8ae-cfbe03f96ea6.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NDR201902130067/10_0a_100a1501-401f-443f-aabb-6f95c166f07c.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NDR201901290116/a3_b6_a3b679dc-be5f-4a71-a26e-a0c343d04148.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NMR202206100127/1b_e2_1be20035-3b26-41af-8099-599d2c38f27c.dcm",
    "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NMR202204150102/3f_cb_3fcb0caf-4077-4672-9553-eb7de0d39e6e.dcm"
]

all_file_data = []
global_keys_list = []

print("🚀 开始读取文件并提取所有物理 Tag 字段...")

# 1. 读取单个文件
for path in file_paths:
    if not os.path.exists(path):
        all_file_data.append(None)
        continue
    try:
        ds = pydicom.dcmread(path, stop_before_pixels=True)
        keys = set()
        for elem in ds:
            tag_str = str(elem.tag)
            name = elem.keyword if elem.keyword else "Private_or_Unknown"
            keys.add(f"{tag_str} [{name}]")
        
        modality_type = getattr(ds, 'Modality', 'Unknown')
        file_name = os.path.basename(path)
        
        all_file_data.append({
            "File_Name": file_name,
            "Modality": modality_type,
            "Field_Count": len(keys),
            "Keys": keys
        })
        global_keys_list.append(keys)
    except Exception as e:
        print(f"❌ 读取文件出错: {path} - {e}")
        all_file_data.append(None)

# 2. 准备 Pandas DataFrame 数据列表
single_stats_data = []
pairwise_data = []

# 单文件数据组装
for item in all_file_data:
    if item is not None:
        single_stats_data.append({
            "File Name": item["File_Name"],
            "Modality": item["Modality"],
            "Total Fields": item["Field_Count"]
        })

# 两两比对数据组装
for i in range(0, len(file_paths), 2):
    if i + 1 >= len(file_paths):
        break
    data_A = all_file_data[i]
    data_B = all_file_data[i+1]
    
    if data_A is None or data_B is None:
        continue
        
    keys_A = data_A["Keys"]
    keys_B = data_B["Keys"]
    
    common_keys = keys_A.intersection(keys_B)
    diff_keys = keys_A.symmetric_difference(keys_B) # 两者不同的字段
    
    # 排序并转为字符串，方便在 Excel 中查看
    common_keys_str = " | ".join(sorted(list(common_keys)))
    diff_keys_str = " | ".join(sorted(list(diff_keys))) if diff_keys else "无差异"
    
    # 判断是否为同一模态
    is_same_modality = "Yes" if data_A["Modality"] == data_B["Modality"] else "No"
    
    pairwise_data.append({
        "Group ID": i // 2 + 1,
        "File A Name": data_A["File_Name"],
        "File A Modality": data_A["Modality"],
        "File A Fields": data_A["Field_Count"],
        "File B Name": data_B["File_Name"],
        "File B Modality": data_B["Modality"],
        "File B Fields": data_B["Field_Count"],
        "Is Same Modality?": is_same_modality,
        "Common Field Count": len(common_keys),
        "Difference Count": len(diff_keys),
        "Common Fields (Detail)": common_keys_str,
        "Differing Fields (Detail)": diff_keys_str
    })

# 全局数据组装
global_common_data = []
if global_keys_list:
    global_common = set.intersection(*global_keys_list)
    for key in sorted(list(global_common)):
        global_common_data.append({"Global Common Field": key})

# 3. 写入 Excel
output_excel_path = "../Temp_data/02_DICOM_Validation_Analysis.xlsx"
print(f"✅ 数据提取完毕，正在生成 Excel 表格: {output_excel_path} ...")

with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
    # 写入两两比对分析 Sheet
    df_pairwise = pd.DataFrame(pairwise_data)
    df_pairwise.to_excel(writer, sheet_name="Pairwise_Analysis", index=False)
    
    # 写入全局共有 Sheet
    df_global = pd.DataFrame(global_common_data)
    df_global.to_excel(writer, sheet_name="Global_Common_Fields", index=False)
    
    # 写入单文件统计 Sheet
    df_single = pd.DataFrame(single_stats_data)
    df_single.to_excel(writer, sheet_name="Single_File_Stats", index=False)

print("🎉 Excel 表格生成成功！请下载并查看。")