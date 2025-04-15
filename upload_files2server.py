import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

LOCAL_DIR = "C:\\Users\\Administrator\\Desktop"
REMOTE_USER = ""
REMOTE_HOST = ""
REMOTE_PORT = ""
REMOTE_DIR = ""

class NewImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"Detected new file: {event.src_path}")
            # 使用 rsync 或 scp 上传
            # 确保你的 SSH 设置允许无密码登录（使用 SSH 密钥）
            remote_target = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}"
            # 使用 rsync:
            # subprocess.run(["rsync", "-avz", event.src_path, remote_target], check=True)
            # 或者使用 scp:
            time.sleep(0.2)  # 等待文件完全写入
            subprocess.run(["scp", f"-P {REMOTE_PORT}", event.src_path, remote_target], check=True)
            print(f"Uploaded {event.src_path} to {remote_target}")

if __name__ == "__main__":
    event_handler = NewImageHandler()
    observer = Observer()
    observer.schedule(event_handler, LOCAL_DIR, recursive=False) # recursive=False 只监控当前目录
    observer.start()
    print(f"Monitoring directory: {LOCAL_DIR} for new files...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
