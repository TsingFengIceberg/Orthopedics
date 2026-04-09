import pydicom

# 替换为你实际的 dcm 文件路径
good_file = "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NCT202306190432/00_1c_001c4f70-e890-47c4-baf6-e4daf1d4d04d.dcm"
bad_file = "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NCT201901300025/00_1b_001b0303-be73-483e-8fbc-6bc5a0a56d04.dcm"

def check_dicom_encoding(filepath):
    ds = pydicom.dcmread(filepath, stop_before_pixels=True)
    ts_uid = ds.file_meta.TransferSyntaxUID
    print(f"文件: {filepath}")
    print(f"传输语法 UID: {ts_uid}")
    print(f"对应编码名称: {ts_uid.name}\n")

print("=== 传输语法对比测试 ===")
check_dicom_encoding(good_file)
check_dicom_encoding(bad_file)