import os

# ================= 配置路径 =================
current_dir = '.'
output_dir = '../Temp_data'
output_filename = '##_All_Scripts_Compiled.md'
output_path = os.path.join(output_dir, output_filename)

print("🚀 启动 Python 脚本一键打包引擎...\n")

# 确保输出目录存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 获取当前打包脚本自己的文件名，防止产生无限套娃
current_script_name = os.path.basename(__file__)

# 初始化 Markdown 内容
compiled_content = "# 📦 骨科项目 Python 脚本全景合集\n\n"
script_count = 0

# 遍历当前目录，并按文件名排序，保证输出的合集井然有序
for filename in sorted(os.listdir(current_dir)):
    if filename.endswith('.py') and filename != current_script_name:
        filepath = os.path.join(current_dir, filename)
        
        try:
            # 读取脚本内容
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 组装 Markdown 格式 (带上文件名标题和代码块包裹)
            compiled_content += f"### 📄 文件名: `{filename}`\n\n"
            compiled_content += "```python\n"
            compiled_content += code
            # 确保代码块结尾有换行，防止格式错乱
            if not code.endswith('\n'):
                compiled_content += "\n"
            compiled_content += "```\n\n---\n\n"
            
            script_count += 1
            print(f"   ✅ 已打包: {filename}")
            
        except Exception as e:
            print(f"   ❌ 读取 {filename} 失败: {e}")

# 将组装好的内容写入 Temp_data 目录
try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(compiled_content)
    
    print("\n" + "="*50)
    print(f"🎉 打包大功告成！共成功合并了 {script_count} 个脚本文件。")
    print(f"💾 输出文件已保存至: {output_path}")
    print("="*50)
    print("👉 下一步：你可以直接把这个 .md 文件丢给我，让我们开始分析功能矩阵吧！")
    
except Exception as e:
    print(f"\n❌ 写入输出文件失败: {e}")