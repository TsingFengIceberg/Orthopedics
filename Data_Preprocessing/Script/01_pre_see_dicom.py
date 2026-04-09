import pydicom
import os

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

all_file_data = [] # 按照原始顺序存储每个文件的提取结果
global_keys_list = [] # 用于最后计算所有文件的全局交集和并集

print("🚀 开始读取文件并提取所有物理 Tag 字段（含私有及空值）...\n")
print("-" * 60)
print("【单个文件提取概况】")

for path in file_paths:
    if not os.path.exists(path):
        print(f"⚠️ 找不到文件: {path}")
        all_file_data.append(None) # 保持索引对齐
        continue
        
    try:
        ds = pydicom.dcmread(path, stop_before_pixels=True)
        keys = set()
        for elem in ds:
            tag_str = str(elem.tag)
            name = elem.keyword if elem.keyword else "Private_or_Unknown"
            keys.add(f"{tag_str} [{name}]")
        
        modality_id = os.path.basename(os.path.dirname(path))
        file_name = os.path.basename(path)
        modality_type = getattr(ds, 'Modality', 'Unknown')
        
        identifier = f"[{modality_type}] {modality_id} / {file_name}"
        
        all_file_data.append({
            "identifier": identifier,
            "keys": keys
        })
        global_keys_list.append(keys)
        print(f"✅ 读取成功: {identifier}  =>  包含 {len(keys)} 个字段")
        
    except Exception as e:
        print(f"❌ 读取文件出错: {path}\n错误信息: {e}")
        all_file_data.append(None)

# ==================== 两两配对分析 ====================
print("\n" + "=" * 60)
print("📊 DICOM 字段严苛验证报告 (前后两两配对分析)")
print("=" * 60)

for i in range(0, len(file_paths), 2):
    if i + 1 >= len(file_paths):
        break
        
    data_A = all_file_data[i]
    data_B = all_file_data[i+1]
    
    if data_A is None or data_B is None:
        print(f"\n⚠️ 第 {i//2 + 1} 组跳过比对，因为存在读取失败的文件。")
        continue
        
    keys_A = data_A["keys"]
    keys_B = data_B["keys"]
    
    common_keys = keys_A.intersection(keys_B)
    all_keys = keys_A.union(keys_B)
    diff_count = len(all_keys) - len(common_keys)
    
    print(f"\n🟢 【第 {i//2 + 1} 组比对】")
    print(f"   文件 A: {data_A['identifier']} (字段数: {len(keys_A)})")
    print(f"   文件 B: {data_B['identifier']} (字段数: {len(keys_B)})")
    print(f"   👉 两人【共有】的字段数量: {len(common_keys)}")
    print(f"   👉 差异字段数量 (并集 - 交集): {diff_count}")
    
    if diff_count > 0:
        diff_keys = keys_A.symmetric_difference(keys_B)
        sample_diff = list(diff_keys)[:5]
        print(f"   ⚠️ 差异字段示例: {sample_diff}")

# ==================== 全局大盘分析 ====================
if global_keys_list:
    global_common = set.intersection(*global_keys_list)
    global_all = set.union(*global_keys_list)
    
    print("\n" + "=" * 60)
    print("🌍 全局大盘数据 (跨越所有 22 个文件)")
    print("=" * 60)
    print(f"👉 所有文件【严格共有】的字段数量 (交集): {len(global_common)}")
    print(f"👉 整个样本集包含的【所有可能】字段数量 (并集): {len(global_all)}")
    print(f"👉 差异字段数量 (并集 - 交集): {len(global_all) - len(global_common)}\n")
    
    print("【全局共有字段完整列表】(22 个文件全部具备的 Tag):")
    print("-" * 40)
    # 按字母/数字顺序排列，方便阅读
    for key in sorted(list(global_common)):
        print(f"  - {key}")
    print("-" * 40)