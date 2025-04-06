import os
import sys
import requests
import hashlib
import shutil
import subprocess
import time
import json

def download_file(url, dest_path):
    """从指定 URL 下载文件到目标路径"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

def calculate_sha256(file_path):
    """计算文件的 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    # 读取 version.json 文件
    version_file = os.path.join(os.path.dirname(__file__), "version.json")
    with open(version_file, "r", encoding="utf-8") as f:
        version_info = json.load(f)

    download_url = version_info["url"]
    expected_sha256 = version_info["sha256"]
    changelog = version_info["changelog"]

    print(f"更新日志: {changelog}")

    # 下载新文件到桌面
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    new_file_path = os.path.join(desktop_path, "键位模拟器_new.exe")
    print("正在下载更新文件...")
    download_file(download_url, new_file_path)

    # 验证文件完整性
    print("正在验证文件完整性...")
    downloaded_sha256 = calculate_sha256(new_file_path)
    if downloaded_sha256 != expected_sha256:
        print("文件校验失败，更新中止！")
        os.remove(new_file_path)
        sys.exit(1)

    # 关闭正在运行的“键位模拟器.exe”
    print("正在关闭正在运行的程序...")
    exe_name = "键位模拟器.exe"
    try:
        os.system(f"taskkill /f /im {exe_name}")
    except Exception as e:
        print(f"关闭程序失败: {e}")

    # 删除旧的“键位模拟器.exe”
    old_file_path = os.path.join(desktop_path, exe_name)
    if os.path.exists(old_file_path):
        os.remove(old_file_path)

    # 重命名新文件为“键位模拟器.exe”
    os.rename(new_file_path, old_file_path)

    # 启动新的“键位模拟器.exe”
    print("正在启动新的程序...")
    subprocess.Popen([old_file_path], shell=True)

    # 删除自身
    print("正在删除更新程序...")
    script_path = os.path.abspath(__file__)
    time.sleep(1)  # 确保脚本退出后再删除
    os.remove(script_path)

if __name__ == "__main__":
    main()