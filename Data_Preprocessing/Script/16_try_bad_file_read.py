import pydicom

bad_file = "/home/wugang/Data/Orthopedics_Dataset/Hospital_Dataset/Image_Dataset/Raw_DICOMS/RK_NCT201901300025/00_1b_001b0303-be73-483e-8fbc-6bc5a0a56d04.dcm"

ds = pydicom.dcmread(bad_file)
# 获取像素矩阵
img_array = ds.pixel_array

print(f"✅ 成功提取像素矩阵！")
print(f"矩阵形状 (Rows, Cols): {img_array.shape}")
print(f"数据类型 (Dtype): {img_array.dtype}")
print(f"像素值范围: Min={img_array.min()}, Max={img_array.max()}")