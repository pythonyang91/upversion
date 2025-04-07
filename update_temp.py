import os
import sys
import requests
import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

# 腾讯云COS配置
COS_BUCKET = "upup-1330116130"
COS_REGION = "ap-guangzhou"
VERSION_URL = f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/upup%2Freleases%2Fversion.json"
APP_NAME = "键位模拟器.exe"

class UpdateError(Exception):
    """自定义更新异常"""
    pass

class DownloadWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("软件更新")
        self.root.geometry("400x200")
        
        # 进度标签
        self.status_label = tk.Label(self.root, text="准备下载更新...", font=('微软雅黑', 10))
        self.status_label.pack(pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)
        
        # 进度百分比
        self.percent_label = tk.Label(self.root, text="0%", font=('微软雅黑', 10))
        self.percent_label.pack()
        
        # 取消按钮
        self.cancel_btn = tk.Button(self.root, text="取消", command=self.cancel_download)
        self.cancel_btn.pack(pady=10)
        
        self.cancel_flag = False
    
    def cancel_download(self):
        self.cancel_flag = True
        self.status_label.config(text="正在取消下载...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def update_progress(self, current, total):
        percent = int((current / total) * 100)
        self.progress["value"] = percent
        self.percent_label.config(text=f"{percent}%")
        self.root.update_idletasks()
    
    def show_error(self, msg):
        messagebox.showerror("更新错误", msg)
        self.root.destroy()
    
    def show_success(self):
        messagebox.showinfo("更新完成", "软件更新已成功完成！")
        self.root.destroy()

def download_with_progress(url, dest_path, window):
    """带进度条的下载函数"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if window.cancel_flag:
                    os.remove(dest_path)
                    raise UpdateError("用户取消了下载")
                
                if chunk:  # 过滤keep-alive chunks
                    file.write(chunk)
                    downloaded += len(chunk)
                    window.update_progress(downloaded, total_size)
        
        return True
    except requests.exceptions.RequestException as e:
        raise UpdateError(f"下载失败: {str(e)}")

def kill_process(process_name):
    """终止正在运行的进程"""
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', process_name], check=True, shell=True)
        else:
            subprocess.run(['pkill', '-f', process_name], check=True)
        time.sleep(1)  # 等待进程完全退出
    except subprocess.CalledProcessError:
        pass  # 进程可能本就不存在

def get_desktop_path():
    """获取桌面路径"""
    return os.path.join(os.path.expanduser("~"), "Desktop")

def run_update(window):
    try:
        window.status_label.config(text="正在获取版本信息...")
        
        # 1. 获取版本信息
        try:
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            version_info = response.json()
        except Exception as e:
            raise UpdateError(f"获取版本信息失败: {str(e)}")
        
        window.status_label.config(text=f"发现新版本 v{version_info.get('version', '未知')}")
        
        # 2. 下载新版本
        download_path = version_info["url"]

        full_url = download_path
        
        desktop = get_desktop_path()
        temp_file = os.path.join(desktop, f"{APP_NAME}.tmp")
        target_file = os.path.join(desktop, APP_NAME)
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        window.status_label.config(text="正在下载更新文件...")
        download_with_progress(full_url, temp_file, window)
        
        # 3. 执行更新
        window.status_label.config(text="正在应用更新...")
        kill_process(APP_NAME)
        
        if os.path.exists(target_file):
            os.remove(target_file)
        
        os.rename(temp_file, target_file)
        
        # 4. 启动新版本
        window.status_label.config(text="正在启动新版本...")
        subprocess.Popen([target_file], shell=True, cwd=desktop)
        
        window.show_success()
        
    except UpdateError as e:
        window.show_error(str(e))
    except Exception as e:
        window.show_error(f"未知错误: {str(e)}")

def main():
    window = DownloadWindow()
    
    # 在新线程中运行更新
    update_thread = Thread(target=lambda: run_update(window))
    update_thread.start()
    
    window.root.mainloop()
    update_thread.join()

if __name__ == "__main__":
    main()