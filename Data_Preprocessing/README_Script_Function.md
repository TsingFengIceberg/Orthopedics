# 📦 数据预处理脚本功能矩阵 (Script Function Matrix)

本矩阵记录了 `Data_Preprocessing/Script` 目录下所有数据清洗、核验与排版脚本的核心功能与运行拓扑关系。部分脚本因逻辑迭代（如从“连坐剔除”升级为“切片级扣减”）存在多个版本，请重点关注标记为“✅”的最终验证版脚本。

| 脚本文件 | 简要功能描述 | 前置脚本 | 后置脚本 | 重要度 |
| :--- | :--- | :--- | :--- | :---: |
| [`01_pre_see_dicom.py`](./Script/01_pre_see_dicom.py) | 探索性测试：读取11对DICOM文件，对比提取的Tag字段差异。 | - | - | |
| [`02_pre_see_dicom_b.py`](./Script/02_pre_see_dicom_b.py) | 增强版探索测试：提取Tag字段差异并导出为Excel分析表。 | `01_pre_see_dicom.py` | - | |
| [`03_pre_try_extract_dicom_data.py`](./Script/03_pre_try_extract_dicom_data.py) | **核心底座**：无视文件后缀物理全量扫描DICOM，提取全量元数据生成JSONL保险箱与CSV宽表。 | - | `04_full_sparse_table_report.py`<br>`05_count_modality.py`<br>`10_clean_and_built_3_meta_table.py` | ✅ |
| [`04_full_sparse_table_report.py`](./Script/04_full_sparse_table_report.py) | 统计宽表各列缺失率及样本值，生成全景评估报告。 | `03_pre_try_extract_dicom_data.py` | - | |
| [`05_count_modality.py`](./Script/05_count_modality.py) | 极速统计宽表中的 Modality 模态全景分布。 | `03_pre_try_extract_dicom_data.py` | - | |
| [`06_full_sparse_table_report_with_modality.py`](./Script/06_full_sparse_table_report_with_modality.py) | 按CT、MR、XRay三大模态拆分，分别统计各模态下字段的缺失率与样本。 | `03_pre_try_extract_dicom_data.py` | - | |
| [`07_see_threshold_result.py`](./Script/07_see_threshold_result.py) | 剔除私有标签，评估保留阈值在10%和50%时的特征存活率。 | `03_pre_try_extract_dicom_data.py` | `08_see_threshold_result_b.py` | |
| [`08_see_threshold_result_b.py`](./Script/08_see_threshold_result_b.py) | 阶梯式（0~50%）测算非空阈值对公共特征保留数量的影响。 | `07_see_threshold_result.py` | `09_see_threshold_result_c.py` | |
| [`09_see_threshold_result_c.py`](./Script/09_see_threshold_result_c.py) | 细化步长（0~100%）动态生成阈值留存测试报告。 | `08_see_threshold_result_b.py` | `10_clean_and_built_3_meta_table.py` | |
| [`10_clean_and_built_3_meta_table.py`](./Script/10_clean_and_built_3_meta_table.py) | **核心基准**：应用5%非空阈值与私有标签剔除规则，生成三大模态(CT/MR/XRay)纯净元数据表。 | `03_pre_try_extract_dicom_data.py`<br>`09_see_threshold_result_c.py` | `11_check_body_part.py`<br>`14_check_unmatched_body_part.py`<br>`19_check_if_left_words.py`<br>`39_3_modality_intersection.py`<br>`50_single_Voxel_FEA_test.py`,<br>`51_single_Voxel_FEA_test_fp16.py`<br>`55_get_dicom_words.py` | ✅ |
| [`11_check_body_part.py`](./Script/11_check_body_part.py) | 对基准表执行部位相关字段（BodyPartExamined等）取值的频次普查。 | `10_clean_and_built_3_meta_table.py` | `12_check_body_keys_cover_range.py` | |
| [`12_check_body_keys_cover_range.py`](./Script/12_check_body_keys_cover_range.py) | 计算不同部位识别字段对数据的增量联合覆盖率。 | `11_check_body_part.py` | `13_check_fuzzy_value.py` | |
| [`13_check_fuzzy_value.py`](./Script/13_check_fuzzy_value.py) | 对CHEST、NECK等模糊部位进行深度采样与交叉印证。 | `12_check_body_keys_cover_range.py` | - | |
| [`14_check_unmatched_body_part.py`](./Script/14_check_unmatched_body_part.py) | 第一版强约束过滤：提取不符合初代脊柱白名单的数据。 | `10_clean_and_built_3_meta_table.py` | `17_extract_unmatched_details.py`<br>`18_new_from_14_check_unmatched_body_part.py` | |
| [`15_see_dicom_encode.py`](./Script/15_see_dicom_encode.py) | DICOM传输语法（TransferSyntaxUID）对比诊断测试。 | - | - | |
| [`16_try_bad_file_read.py`](./Script/16_try_bad_file_read.py) | 尝试硬解析损坏DICOM文件的像素矩阵。 | - | - | |
| [`17_extract_unmatched_details.py`](./Script/17_extract_unmatched_details.py) | 统计不符合条件数据的文件夹层级影响（连坐扣减演示分析）。 | `14_check_unmatched_body_part.py` | - | |
| [`18_new_from_14_check_unmatched_body_part.py`](./Script/18_new_from_14_check_unmatched_body_part.py) | 迭代过滤逻辑：全量打印不符合新白名单的数据供审阅。 | `14_check_unmatched_body_part.py` | `22_new_from_18_14_check_unmatched_body_part.py` | |
| [`19_check_if_left_words.py`](./Script/19_check_if_left_words.py) | 初代双向兜底测试：寻找既不在白名单也不在黑名单的孤儿数据。 | `10_clean_and_built_3_meta_table.py` | `20_check_if_left_words_again.py` | |
| [`20_check_if_left_words_again.py`](./Script/20_check_if_left_words_again.py) | 迭代双向兜底测试：更新黑白名单后的孤儿数据排查。 | `19_check_if_left_words.py` | `21_check_if_left_words_again_again.py` | |
| [`21_check_if_left_words_again_again.py`](./Script/21_check_if_left_words_again_again.py) | 修复空值(NAN)判定Bug的终极兜底测试。 | `20_check_if_left_words_again.py` | `22_new_from_18_14_check_unmatched_body_part.py` | |
| [`22_new_from_18_14_check_unmatched_body_part.py`](./Script/22_new_from_18_14_check_unmatched_body_part.py) | **核心黑名单**：基于最终黑白名单生成精确切片级废片列表。 | `18_new_from_14_check_unmatched_body_part.py`<br>`21_check_if_left_words_again_again.py` | `23_check_clean_data_if_all_words_nan.py`<br>`39_3_modality_intersection.py`<br>`48_new_47.py`<br>`50_single_Voxel_FEA_test.py`<br>`51_single_Voxel_FEA_test_fp16.py` | ✅ |
| [`23_check_clean_data_if_all_words_nan.py`](./Script/23_check_clean_data_if_all_words_nan.py) | 留存合规数据完整性校验，拦截全空盲盒。 | `22_new_from_18_14_check_unmatched_body_part.py` | - | |
| [`25_reorder_source_raw_tables.py`](./Script/25_reorder_source_raw_tables.py) | **临床底盘**：按患者ID与时间维度对所有非检验临床表执行全局时序升序重排。 | - | `38_5_way_patient_intersections.py`<br>`41_create_full_inforamtion_grade_annotation_table.py` | ✅ |
| [`26_lab_item_count.py`](./Script/26_lab_item_count.py) | 全量扫描三大检验表，输出包含数万检验频次的原始指标总字典。 | - | `27_lab_items_mapping.py` | |
| [`27_lab_items_mapping.py`](./Script/27_lab_items_mapping.py) | 初版检验字典：利用名称脱水与同名折叠规则生成初始映射表。 | `26_lab_item_count.py` | `28_refresh_mapping_draft.py` | |
| [`28_refresh_mapping_draft.py`](./Script/28_refresh_mapping_draft.py) | 引入人工预设的初版安全白名单，修正过度合并问题。 | `27_lab_items_mapping.py` | `29_refresh_mapping_draft_again_2.py` | |
| [`29_refresh_mapping_draft_again_2.py`](./Script/29_refresh_mapping_draft_again_2.py) | V4审查版：首次引入绿/黄/灰三色视觉分块输出，供医生查阅。 | `28_refresh_mapping_draft.py` | `30_refresh_mapping_draft_again_3.py` | |
| [`30_refresh_mapping_draft_again_3.py`](./Script/30_refresh_mapping_draft_again_3.py) | V6修复版：恢复全部安全指标合并关系并优化边框视觉排版。 | `29_refresh_mapping_draft_again_2.py` | `31_lab_words_collision_detection.py` | |
| [`31_lab_words_collision_detection.py`](./Script/31_lab_words_collision_detection.py) | 动态同源防撞探针：扫描检验大表并输出合并组合是否会在同患者同时刻造成重叠冲突。 | `30_refresh_mapping_draft_again_3.py` | `32_final_mapping_generator.py` | |
| [`32_final_mapping_generator.py`](./Script/32_final_mapping_generator.py) | **核心规则**：综合防撞结果生成最终视觉排版无损检验指标映射大表。 | `31_lab_words_collision_detection.py` | `33_check_is_all_mapped.py`<br>`34_mapping_Deduplicating_and_find_collision.py` | ✅ |
| [`33_check_is_all_mapped.py`](./Script/33_check_is_all_mapped.py) | 绝对壁垒审计：验证底表所有指标是否100%被字典收录。 | `32_final_mapping_generator.py` | - | |
| [`34_mapping_Deduplicating_and_find_collision.py`](./Script/34_mapping_Deduplicating_and_find_collision.py) | **核心清洗**：执行四级漏斗强力清洗（去重/映射合并/致命硬剔除），输出极净检验长表。 | `32_final_mapping_generator.py` | `35_create_lab_wide_table.py` | ✅ |
| [`35_create_lab_wide_table.py`](./Script/35_create_lab_wide_table.py) | **核心降维**：将清洗长表通过Pivot操作转换为ML-Ready稀疏大宽表。 | `34_mapping_Deduplicating_and_find_collision.py` | `38_5_way_patient_intersections.py`<br>`49_lab_indicator_macro_stats.py` | ✅ |
| [`36_extract_dicom_modality_ids.py`](./Script/36_extract_dicom_modality_ids.py) | 物理盘点：抓取硬盘上真实存在的 DICOM 文件夹名。 | - | `37_cross_reference_image_mapping.py` | |
| [`37_cross_reference_image_mapping.py`](./Script/37_cross_reference_image_mapping.py) | **核对枢纽**：执行硬盘物理存在与 HIS 账单的双向交集核对，生成合规交集底座。 | `36_extract_dicom_modality_ids.py` | `38_5_way_patient_intersections.py`<br>`39_3_modality_intersection.py` | ✅ |
| [`38_5_way_patient_intersections.py`](./Script/38_5_way_patient_intersections.py) | 五维全景分析：影像、临床、护理、疼痛、化验的大满贯患者重合度统计。 | `25_reorder_source_raw_tables.py`<br>`35_create_lab_wide_table.py`<br>`37_cross_reference_image_mapping.py` | - | ✅ |
| [`39_3_modality_intersection.py`](./Script/39_3_modality_intersection.py) | **核心统计**：利用UID切片级精确扣减引流，盘点三模态（Has_CT等）交集分布及包含组合。 | `10_clean_and_built_3_meta_table.py`<br>`22_new_from_18_14_check_unmatched_body_part.py`<br>`37_cross_reference_image_mapping.py` | - | ✅ |
| [`40_create_fracture_grade_annotation_table.py`](./Script/40_create_fracture_grade_annotation_table.py) | 基于宽容UID过滤逻辑的极简骨折分级标注模板（仅含ID与空白列）生成器。 | `37_cross_reference_image_mapping.py` | - | |
| [`41_create_full_inforamtion_grade_annotation_table.py`](./Script/41_create_full_inforamtion_grade_annotation_table.py) | **终极排版**：按首诊时间严格排序的多模态临床影像合并全景时间轴模板（搭载切片级精准过滤防线）。 | `25_reorder_source_raw_tables.py`<br>`37_cross_reference_image_mapping.py` | - | ✅ |
| [`42_create_new_format_annotation_table.py`](./Script/42_create_new_format_annotation_table.py) | **终极排版**：支持视觉高亮的灵活分行全景模板，搭载防连坐UID精确过滤与临床汇总功能。 | `25_reorder_source_raw_tables.py`<br>`37_cross_reference_image_mapping.py` | - | ✅ |
| [`43_find_image_patients_count_again.py`](./Script/43_find_image_patients_count_again.py) | 尝试性物理全量读取统计：由于只读头文件，用于印证CT数据的总盘。 | - | - | |
| [`44_count_dicom_modality_again.py`](./Script/44_count_dicom_modality_again.py) | 第二次全物理扫描：强制读取（包括损坏头文件）以统计真实的医院模态构成。 | - | `45_find_image_patients_count_again_2.py` | |
| [`45_find_image_patients_count_again_2.py`](./Script/45_find_image_patients_count_again_2.py) | 基于44号绝对快照表的模态宽容组合患者再次印证。 | `44_count_dicom_modality_again.py` | - | |
| [`46_count_10_meta_data_table.py`](./Script/46_count_10_meta_data_table.py) | 统计最终10号清洗基底存活的总照片数。 | `10_clean_and_built_3_meta_table.py` | - | |
| [`47_find_truth_wrong_logitic.py`](./Script/47_find_truth_wrong_logitic.py) | *历史遗留版本*：导致数据大规模“连坐误杀”的错误旧版交叉验证统计引擎。 | - | `48_new_47.py` | |
| [`48_new_47.py`](./Script/48_new_47.py) | **核心基盘测试**：彻底修复连坐Bug的最新 UID **切片级**交叉核验引擎，成功保全全部合法患者。 | `10_clean_and_built_3_meta_table.py`<br>`22_new_from_18_14_check_unmatched_body_part.py` | - | ✅ |
| [`49_lab_indicator_macro_stats.py`](./Script/49_lab_indicator_macro_stats.py) | **特征普查**：对检验大宽表的所有指标进行总检验频次与独立患者覆盖率的宏观统计，辅助特征工程筛选。 | `35_create_lab_wide_table.py` | - | ✅ |
| [`50_single_Voxel_FEA_test.py`](./Script/50_single_Voxel_FEA_test.py) | **终端压测**：集成2.0x重采样、4090 D力学演化、智能Bounding Box裁剪与HDF5无损验证的终极存储评测方案。 | `10_clean_and_built_3_meta_table.py`<br>`22_new_from_18_14_check_unmatched_body_part.py` | - | ✅ |
| [`51_single_Voxel_FEA_test_fp16.py`](./Script/51_single_Voxel_FEA_test_fp16.py) | **精度压测**：针对1497例全量数据进行FP16极限压缩，评估精度损失与空间重构误差。 | `10_clean_and_built_3_meta_table.py` | `52_h5_to_nifti_visualizer.py` | ✅ |
| [`52_h5_to_nifti_visualizer.py`](./Script/52_h5_to_nifti_visualizer.py) | **格式转换**：将HDF5保险箱数据转为NIfTI (.nii.gz)，解决Float16不兼容可视化软件的痛点。 | `50_benchmark_2_ultimate.py`<br>`51_single_Voxel_FEA_test_fp16.py` | `54_transfer2stl.py` | |
| [`53_see_fast.py`](./Script/53_see_fast.py) | **快速比对**：生成FP32与FP16版本的MIP（最大密度投影）与中心切面对比图，直观验证压缩效果。 | `50_benchmark_2_ultimate.py`<br>`51_single_Voxel_FEA_test_fp16.py` | - | |
| [`54_transfer2stl.py`](./Script/54_transfer2stl.py) | **傻瓜化导出**：将NIfTI转为STL格式，内置降采样逻辑以适配Windows原生3D查看器。 | `52_h5_to_nifti_visualizer.py` | - | |
| [`55_get_dicom_words.py`](./Script/55_get_dicom_words.py) | **字段提取**：从10号清洗表中垂直提取所有DICOM关键字，用于分析坐标系偏移与物理参数。 | `10_clean_and_built_3_meta_table.py` | - | ✅ |
| [`56_fast_export_3D_test.py`](./Script/56_fast_export_3D_test.py) | **极速预览版**：实现0.5x降采样、物理坐标系校准，快速导出不断层、不压扁的H5与STL双轨文件。 | `10_clean_and_built_3_meta_table.py` | `57_balanced_export_3D_test.py` | |
| [`57_balanced_export_3D_test.py`](./Script/57_balanced_export_3D_test.py) | **最终验证版**：高清满血导出引擎。支持Float32、形态学闭运算愈合（补洞）、孤岛剔除与Taubin平滑。 | `10_clean_and_built_3_meta_table.py`<br>`55_get_dicom_words.py` | - | ✅ |