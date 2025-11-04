import os
import sys
import requests
import threading
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
from io import BytesIO
import urllib.parse
import shutil
import queue
import datetime
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置程序根目录
ROOT_DIR = Path(__file__).parent.absolute()

# 确保使用项目根目录下的Python环境
PYTHON_DIR = ROOT_DIR / "python"
if PYTHON_DIR.exists():
    # 将项目Python路径添加到系统路径的开头
    sys.path.insert(0, str(PYTHON_DIR))
    sys.path.insert(0, str(PYTHON_DIR / "Lib" / "site-packages"))


class PexelsVideoDownloader:
    def __init__(self):
        # 设置API密钥
        self.api_key = "yUrBGA7OtS1WxL7s18Aliqd0jYUOWw65RE3kqJ9Ulve5RPfVmL9ineAy"
        self.base_url = "https://api.pexels.com/videos"
        
        # 日志队列
        self.log_queue = queue.Queue()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("Pexels 4K 视频下载器 - 增强版")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 750)
        
        # 创建变量
        self.search_query = tk.StringVar()
        self.selected_videos = []
        self.video_thumbnails = []
        self.thumbnail_frames = []
        self.page = 1  # 当前页码
        self.per_page = 30  # 每页显示的视频数量
        self.current_videos = []  # 当前显示的视频
        self.total_results = 0  # 总结果数
        self.min_width = tk.StringVar(value="3840")  # 默认最小宽度3840
        self.min_height = tk.StringVar(value="2160")  # 默认最小高度2160
        
        # 常用搜索关键词
        self.common_keywords = [
            ("Nature", "大自然"), 
            ("Ocean", "海洋"), 
            ("Mountains", "山脉"), 
            ("Forest", "森林"),
            ("Animals", "动物"), 
            ("City", "城市"), 
            ("Technology", "科技"), 
            ("Food", "食物"),
            ("Travel", "旅行"), 
            ("Sports", "运动"), 
            ("Music", "音乐"), 
            ("Business", "商业")
        ]
        
        # 设置下载目录为桌面
        desktop = Path.home() / "Desktop" / "Pexels_Videos"
        self.download_dir = desktop
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建UI
        self.create_widgets()
        
        # 启动日志处理器
        self.start_log_processor()
        
        # 初始化日志
        self.log_message("Pexels 4K 视频下载器增强版已启动")
        self.log_message(f"默认下载目录: {self.download_dir}")
        self.log_message("默认最小分辨率: 3840×2160")
        self.log_message("提示: 使用英文关键词通常能获得更多的搜索结果")
        
        # 搜索历史
        self.search_history = []
        self.max_history = 10  # 最大历史记录数
        
    def log_message(self, message):
        """添加日志消息到队列"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_queue.put(formatted_message)
        
    def start_log_processor(self):
        """启动日志处理器"""
        self.process_log_queue()
        
    def process_log_queue(self):
        """处理日志队列中的消息"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
        except queue.Empty:
            pass
        # 每100毫秒检查一次新日志
        self.root.after(100, self.process_log_queue)
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部框架 - 搜索和目录设置
        top_frame = ttk.LabelFrame(main_frame, text="搜索和设置")
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # 搜索框架
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(fill="x", pady=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side="left", padx=(10, 5))
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_query, width=20)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda event: self.search_videos())
        # 添加搜索建议功能
        self.search_entry.bind("<KeyRelease>", self.on_search_key_release)
        
        # 常用关键词按钮
        keyword_frame = ttk.Frame(search_frame)
        keyword_frame.pack(side="left", padx=10)
        
        ttk.Label(keyword_frame, text="常用:").pack(side="left")
        nature_btn = ttk.Button(keyword_frame, text="Nature", width=8, 
                               command=lambda: self.set_search_keyword("Nature"))
        nature_btn.pack(side="left", padx=2)
        ocean_btn = ttk.Button(keyword_frame, text="Ocean", width=8,
                              command=lambda: self.set_search_keyword("Ocean"))
        ocean_btn.pack(side="left", padx=2)
        city_btn = ttk.Button(keyword_frame, text="City", width=8,
                             command=lambda: self.set_search_keyword("City"))
        city_btn.pack(side="left", padx=2)
        
        search_btn = ttk.Button(search_frame, text="搜索", command=self.search_videos)
        search_btn.pack(side="left", padx=5)
        
        # 分辨率筛选
        res_frame = ttk.Frame(search_frame)
        res_frame.pack(side="left", padx=10)
        
        ttk.Label(res_frame, text="最小分辨率:").pack(side="left")
        ttk.Label(res_frame, text="宽≥").pack(side="left", padx=(5, 0))
        width_entry = ttk.Entry(res_frame, textvariable=self.min_width, width=6)
        width_entry.pack(side="left", padx=2)
        ttk.Label(res_frame, text="高≥").pack(side="left", padx=(5, 0))
        height_entry = ttk.Entry(res_frame, textvariable=self.min_height, width=6)
        height_entry.pack(side="left", padx=2)
        
        # 添加默认值提示
        default_tip = ttk.Label(res_frame, text="(默认3840×2160)", foreground="gray")
        default_tip.pack(side="left", padx=(5, 0))
        
        # 页面控制框架
        page_frame = ttk.Frame(search_frame)
        page_frame.pack(side="left", padx=10)
        
        self.prev_btn = ttk.Button(page_frame, text="上一页", command=self.prev_page, state="disabled")
        self.prev_btn.pack(side="left", padx=(0, 5))
        
        self.page_label = ttk.Label(page_frame, text="第 1 页")
        self.page_label.pack(side="left", padx=5)
        
        self.next_btn = ttk.Button(page_frame, text="下一页", command=self.next_page, state="disabled")
        self.next_btn.pack(side="left", padx=(5, 0))
        
        # 自定义页码跳转
        goto_frame = ttk.Frame(page_frame)
        goto_frame.pack(side="left", padx=(10, 0))
        
        ttk.Label(goto_frame, text="跳转到:").pack(side="left")
        self.page_var = tk.StringVar(value="1")
        page_entry = ttk.Entry(goto_frame, textvariable=self.page_var, width=5)
        page_entry.pack(side="left", padx=2)
        page_entry.bind("<Return>", lambda event: self.goto_page())
        
        goto_btn = ttk.Button(goto_frame, text="GO", command=self.goto_page, width=4)
        goto_btn.pack(side="left", padx=(2, 0))
        
        # 结果统计
        self.result_label = ttk.Label(search_frame, text="共 0 个结果")
        self.result_label.pack(side="left", padx=10)
        
        # 目录设置框架
        dir_frame = ttk.Frame(top_frame)
        dir_frame.pack(fill="x", pady=5)
        
        ttk.Label(dir_frame, text="下载目录:").pack(side="left", padx=(10, 5))
        self.dir_entry = ttk.Entry(dir_frame, width=30)
        self.dir_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.dir_entry.insert(0, str(self.download_dir))
        
        browse_btn = ttk.Button(dir_frame, text="浏览", command=self.browse_directory, width=8)
        browse_btn.pack(side="left", padx=5)
        
        # 批量操作框架
        batch_frame = ttk.Frame(top_frame)
        batch_frame.pack(fill="x", pady=5)
        
        ttk.Label(batch_frame, text="批量操作:").pack(side="left", padx=(10, 5))
        select_all_btn = ttk.Button(batch_frame, text="全选当前页", command=self.select_all)
        select_all_btn.pack(side="left", padx=5)
        
        deselect_all_btn = ttk.Button(batch_frame, text="取消全选", command=self.deselect_all)
        deselect_all_btn.pack(side="left", padx=5)
        
        # 搜索提示
        tip_frame = ttk.Frame(top_frame)
        tip_frame.pack(fill="x", pady=5)
        
        tip_label = ttk.Label(tip_frame, 
                             text="💡 提示: 使用英文关键词通常能获得更多的搜索结果，如 'Nature' 比 '大自然' 结果更多",
                             foreground="blue")
        tip_label.pack(side="left", padx=10)
        
        # 结果框架
        results_frame = ttk.LabelFrame(main_frame, text="搜索结果")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Canvas和滚动条来显示缩略图
        canvas_frame = ttk.Frame(results_frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind("<Button-5>", self._on_mousewheel_linux)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="x", padx=5, pady=5)
        
        # 日志文本框
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_text_frame, height=8, state="normal")
        self.log_text.pack(fill="both", expand=True)
        
        # 日志操作按钮
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill="x", padx=5, pady=5)
        
        copy_log_btn = ttk.Button(log_button_frame, text="复制日志", command=self.copy_logs)
        copy_log_btn.pack(side="left", padx=(0, 10))
        
        clear_log_btn = ttk.Button(log_button_frame, text="清空日志", command=self.clear_logs)
        clear_log_btn.pack(side="left")
        
        # 底部框架 - 下载按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", padx=5, pady=5)
        
        self.download_btn = ttk.Button(bottom_frame, text="下载选中视频", command=self.download_selected, state="disabled")
        self.download_btn.pack(pady=10)
        
        # 状态标签
        self.status_label = ttk.Label(bottom_frame, text="就绪")
        self.status_label.pack(pady=(0, 5))
        
    def on_search_key_release(self, event):
        """处理搜索框按键释放事件，提供搜索建议"""
        query = self.search_query.get().strip().lower()
        if len(query) >= 2:  # 当输入至少2个字符时提供搜索建议
            suggestions = [kw[0] for kw in self.common_keywords if query in kw[0].lower() or query in kw[1]]
            if suggestions and event.keysym not in ['Up', 'Down', 'Return']:
                # 简单的搜索建议提示（可以扩展为下拉列表）
                if not hasattr(self, '_suggestion_shown') or not self._suggestion_shown:
                    self.log_message(f"搜索建议: {', '.join(suggestions[:3])}")
                    self._suggestion_shown = True
        else:
            self._suggestion_shown = False
    
    def set_search_keyword(self, keyword):
        """设置搜索关键词"""
        self.search_query.set(keyword)
        self.page = 1  # 重置页码
        self.search_videos()
        
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件 (Windows)"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _on_mousewheel_linux(self, event):
        """处理鼠标滚轮事件 (Linux)"""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        
    def browse_directory(self):
        """浏览并选择下载目录"""
        directory = filedialog.askdirectory(initialdir=self.download_dir)
        if directory:
            self.download_dir = Path(directory)
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, str(self.download_dir))
            self.log_message(f"下载目录已更改为: {self.download_dir}")
    
    def select_all(self):
        """全选当前页"""
        for video in self.current_videos:
            var = video.get("selection_var")
            if var and not var.get():
                var.set(True)
                # 检查是否已经存在于选中列表中
                video_id = video.get("id")
                if not any(v.get("id") == video_id for v in self.selected_videos):
                    self.selected_videos.append(video)
        
        # 更新下载按钮状态
        if self.selected_videos:
            self.download_btn.config(state="normal")
            self.download_btn.config(text=f"下载选中视频 ({len(self.selected_videos)})")
        self.log_message(f"已选择 {len(self.current_videos)} 个视频")
    
    def deselect_all(self):
        """取消全选"""
        for video in self.current_videos:
            var = video.get("selection_var")
            if var and var.get():
                var.set(False)
        
        # 从选中列表中移除当前页的视频
        current_ids = [v.get("id") for v in self.current_videos]
        self.selected_videos = [v for v in self.selected_videos if v.get("id") not in current_ids]
        
        if not self.selected_videos:
            self.download_btn.config(state="disabled")
        self.download_btn.config(text="下载选中视频")
        self.log_message("已取消当前页选择")
    
    def search_videos(self):
        query = self.search_query.get().strip()
        if not query:
            self.status_label.config(text="请输入搜索关键词")
            self.log_message("搜索失败: 请输入搜索关键词")
            return
            
        # 添加到搜索历史
        if query not in self.search_history:
            self.search_history.append(query)
            if len(self.search_history) > self.max_history:
                self.search_history.pop(0)
            
        self.log_message(f"开始搜索视频: {query} (第 {self.page} 页)")
        self.status_label.config(text="正在搜索...")
        self.root.update()
        
        # 使用后台线程执行搜索，避免UI卡顿
        search_thread = threading.Thread(target=self._search_videos_thread, daemon=True)
        search_thread.start()
        
    def _search_videos_thread(self):
        """在后台线程中执行搜索"""
        query = self.search_query.get().strip()
        if not query:
            self.root.after(0, lambda: self.status_label.config(text="请输入搜索关键词"))
            self.root.after(0, lambda: self.log_message("搜索失败: 请输入搜索关键词"))
            return
            
        try:
            # 清除之前的搜索结果（在UI线程中执行）
            self.root.after(0, self.clear_thumbnails)
            
            # 构建API请求
            url = f"{self.base_url}/search"
            headers = {"Authorization": self.api_key}
            params = {
                "query": query,
                "per_page": self.per_page,
                "page": self.page,
                "orientation": "landscape"
            }
            
            # 只有当设置了分辨率筛选时才添加这些参数
            try:
                min_w = int(self.min_width.get())
                min_h = int(self.min_height.get())
                if min_w > 0 or min_h > 0:
                    if min_w > 0:
                        params["min_width"] = min_w
                    if min_h > 0:
                        params["min_height"] = min_h
            except ValueError:
                pass  # 如果输入不是数字，忽略筛选
            
            self.root.after(0, lambda: self.log_message(f"发送API请求: {url} with params {params}"))
            
            # 设置更短的超时时间以提高响应速度
            response = requests.get(url, headers=headers, params=params, timeout=5)
            self.root.after(0, lambda: self.log_message(f"API响应状态码: {response.status_code}"))
            
            if response.status_code == 401:
                self.root.after(0, lambda: self.status_label.config(text="API密钥无效，请检查密钥设置"))
                self.root.after(0, lambda: self.log_message("搜索失败: API密钥无效"))
                return
            elif response.status_code == 429:
                self.root.after(0, lambda: self.status_label.config(text="API请求过于频繁，请稍后再试"))
                self.root.after(0, lambda: self.log_message("搜索失败: API请求频率限制"))
                return
            elif response.status_code != 200:
                self.root.after(0, lambda: self.status_label.config(text=f"API请求失败: {response.status_code}"))
                self.root.after(0, lambda: self.log_message(f"搜索失败: API请求失败 {response.status_code}"))
                return
                
            data = response.json()
            
            # 在UI线程中处理结果
            self.root.after(0, lambda: self._process_search_results(data))
            
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.status_label.config(text="搜索超时(5秒)，请重试"))
            self.root.after(0, lambda: self.log_message("搜索失败: 请求超时"))
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: self.status_label.config(text=f"网络错误: {str(e)}"))
            self.root.after(0, lambda: self.log_message(f"搜索失败: 网络错误 - {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"搜索出错: {str(e)}"))
            self.root.after(0, lambda: self.log_message(f"搜索出错: {str(e)}"))
            import traceback
            self.root.after(0, lambda: self.log_message(f"详细错误信息: {traceback.format_exc()}"))

    def _process_search_results(self, data):
        """在UI线程中处理搜索结果"""
        videos = data.get("videos", [])
        total_results = data.get("total_results", 0)
        
        self.log_message(f"API返回数据: 找到 {len(videos)} 个视频，总共 {total_results} 个结果")
        
        if not videos:
            self.status_label.config(text="未找到相关视频")
            self.log_message("搜索完成: 未找到相关视频")
            self.next_btn.config(state="disabled")
            return
            
        # 保存当前视频数据
        self.current_videos = videos
        self.total_results = total_results
        
        # 显示视频缩略图
        self._display_videos_ui(videos)
        
    def _display_videos_ui(self, videos):
        """在UI线程中显示视频"""
        # 显示视频缩略图
        self.display_videos(videos)
        self.status_label.config(text=f"找到 {len(videos)} 个视频 (第 {self.page} 页)")
        self.log_message(f"搜索完成: 找到 {len(videos)} 个视频，总共 {self.total_results} 个结果")
        
        # 更新页面控制
        self.update_page_controls()
        
    def prev_page(self):
        """上一页"""
        if self.page > 1:
            self.page -= 1
            self.search_videos()
        
    def next_page(self):
        """下一页"""
        self.page += 1
        self.search_videos()
        
    def goto_page(self):
        """跳转到指定页面"""
        try:
            page_num = int(self.page_var.get())
            if page_num > 0:
                self.page = page_num
                self.search_videos()
            else:
                self.status_label.config(text="页码必须大于0")
                self.root.after(1500, lambda: self.status_label.config(text="就绪"))
        except ValueError:
            self.status_label.config(text="请输入有效的页码")
            self.root.after(1500, lambda: self.status_label.config(text="就绪"))
        
    def update_page_controls(self):
        """更新页面控制按钮状态"""
        self.page_label.config(text=f"第 {self.page} 页")
        self.page_var.set(str(self.page))  # 同步更新页码输入框
        self.prev_btn.config(state="normal" if self.page > 1 else "disabled")
        self.next_btn.config(state="normal" if len(self.current_videos) == self.per_page else "disabled")
        self.result_label.config(text=f"共 {self.total_results} 个结果")
        
    def copy_logs(self):
        """复制日志到剪贴板"""
        logs = self.log_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(logs)
        self.log_message("运行日志已复制到剪贴板")
        
    def clear_logs(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")
        self.log_message("日志已清空")
        
    def clear_thumbnails(self):
        for frame in self.thumbnail_frames:
            frame.destroy()
        self.thumbnail_frames = []
        self.video_thumbnails = []
        # 不清除selected_videos，因为可能跨页面选择
    
    def display_videos(self, videos):
        # 清除之前的缩略图框架
        for frame in self.thumbnail_frames:
            frame.destroy()
        self.thumbnail_frames = []
        self.video_thumbnails = []
        
        # 创建网格布局显示缩略图 (每行4个，减少一行以适应界面)
        for i, video in enumerate(videos):
            row = i // 4
            col = i % 4
            
            # 创建视频框架
            video_frame = ttk.Frame(self.scrollable_frame, relief="raised", borderwidth=2)
            video_frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.thumbnail_frames.append(video_frame)
            
            # 获取视频缩略图 (使用更小的缩略图以提高加载速度)
            thumbnail_url = None
            video_files = video.get("video_files", [])
            image_url = video.get("image", "")  # 使用视频的封面图片
            
            if image_url:
                thumbnail_url = image_url
            elif video_files:
                # 寻找图片预览
                for file in video_files:
                    if file.get("type") == "preview":
                        thumbnail_url = file.get("link")
                        break
                # 如果没有preview类型，则使用第一个文件的链接
                if not thumbnail_url and video_files:
                    thumbnail_url = video_files[0].get("link")
            
            # 异步加载缩略图以避免阻塞UI
            if thumbnail_url:
                # 在后台线程中加载缩略图
                thumbnail_thread = threading.Thread(
                    target=self._load_thumbnail, 
                    args=(thumbnail_url, video_frame, video),
                    daemon=True
                )
                thumbnail_thread.start()
            else:
                # 如果没有缩略图，显示占位符
                self.root.after(0, lambda vf=video_frame: self._show_placeholder(vf, video))
    
    def _load_thumbnail(self, thumbnail_url, video_frame, video):
        """在后台线程中加载缩略图"""
        try:
            # 添加User-Agent避免被拒绝
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # 设置更短的超时时间以提高响应速度
            response = requests.get(thumbnail_url, timeout=5, headers=headers)
            response.raise_for_status()
            
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            
            # 转换为RGB模式（防止RGBA模式问题）
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # 使用更小的尺寸以提高加载速度
            img = img.resize((160, 90), Image.LANCZOS)
            
            # 在UI线程中显示缩略图
            self.root.after(0, lambda: self._display_thumbnail(img, video_frame, video))
        except Exception as e:
            # 在UI线程中显示占位符
            self.root.after(0, lambda: self._show_placeholder(video_frame, video))
    
    def _display_thumbnail(self, img, video_frame, video):
        """在UI线程中显示缩略图"""
        try:
            thumbnail_img = ImageTk.PhotoImage(img)
            self.video_thumbnails.append(thumbnail_img)
            
            img_label = tk.Label(video_frame, image=thumbnail_img)
            img_label.pack(pady=(10, 5))
            
            # 显示视频信息
            self._show_video_info(video_frame, video)
        except Exception as e:
            self.log_message(f"显示缩略图失败: {e}")
            self._show_placeholder(video_frame, video)
    
    def _show_placeholder(self, video_frame, video):
        """显示占位符"""
        try:
            placeholder = tk.Label(video_frame, text="无预览图", width=22, height=5, bg="#e0e0e0")
            placeholder.pack(pady=(10, 5))
            
            # 显示视频信息
            self._show_video_info(video_frame, video)
        except Exception as e:
            self.log_message(f"显示占位符失败: {e}")
    
    def _show_video_info(self, video_frame, video):
        """显示视频信息"""
        try:
            # 视频信息
            video_id = video.get("id", "N/A")
            duration = video.get("duration", "N/A")
            width = video.get("width", "N/A")
            height = video.get("height", "N/A")
            
            info_text = f"ID: {video_id}\n时长: {duration}秒\n分辨率: {width}x{height}"
            info_label = tk.Label(video_frame, text=info_text, justify="left", font=("Arial", 8))
            info_label.pack(pady=(0, 5))
            
            # 选择复选框
            var = tk.BooleanVar()
            # 检查该视频是否已经被选中
            is_selected = any(v.get("id") == video_id for v in self.selected_videos)
            var.set(is_selected)
            
            checkbox = ttk.Checkbutton(
                video_frame, 
                text="选择下载", 
                variable=var,
                command=lambda v=var, vid=video: self.toggle_video_selection(v, vid)
            )
            checkbox.pack(pady=(0, 10))
            
            # 保存视频信息
            video["selection_var"] = var
        except Exception as e:
            self.log_message(f"显示视频信息失败: {e}")
    
    def toggle_video_selection(self, var, video):
        video_id = video.get("id")
        
        if var.get():
            # 检查是否已经存在于选中列表中
            if not any(v.get("id") == video_id for v in self.selected_videos):
                self.selected_videos.append(video)
        else:
            # 从选中列表中移除
            self.selected_videos = [v for v in self.selected_videos if v.get("id") != video_id]
        
        # 更新下载按钮状态
        if self.selected_videos:
            self.download_btn.config(state="normal")
            self.download_btn.config(text=f"下载选中视频 ({len(self.selected_videos)})")
        else:
            self.download_btn.config(state="disabled")
            self.download_btn.config(text="下载选中视频")
    
    def download_selected(self):
        if not self.selected_videos:
            self.status_label.config(text="请选择要下载的视频")
            self.log_message("下载失败: 请选择要下载的视频")
            return
            
        # 更新下载目录
        try:
            self.download_dir = Path(self.dir_entry.get())
            self.download_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_message(f"下载目录错误: {e}")
            messagebox.showerror("错误", f"下载目录设置错误: {e}")
            return
            
        self.log_message(f"开始下载 {len(self.selected_videos)} 个视频到: {self.download_dir}")
        self.status_label.config(text=f"开始下载 {len(self.selected_videos)} 个视频...")
        self.download_btn.config(state="disabled")
        
        # 创建下载进度窗口
        self.create_download_progress_window()
        
        # 使用多线程下载
        download_thread = threading.Thread(target=self.download_videos_thread)
        download_thread.daemon = True
        download_thread.start()
    
    def create_download_progress_window(self):
        """创建下载进度窗口"""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("下载进度")
        self.progress_window.geometry("500x400")
        self.progress_window.resizable(False, False)
        
        # 居中显示
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        # 创建进度框架
        progress_frame = ttk.Frame(self.progress_window, padding="20")
        progress_frame.pack(fill="both", expand=True)
        
        # 总进度
        ttk.Label(progress_frame, text="总进度:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.total_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.total_progress.pack(pady=(5, 15))
        self.total_progress_label = ttk.Label(progress_frame, text="0/0")
        self.total_progress_label.pack()
        
        # 视频列表框架
        list_frame = ttk.LabelFrame(progress_frame, text="视频下载进度", padding="10")
        list_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # 创建Canvas和滚动条
        canvas = tk.Canvas(list_frame, height=200)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_progress_frame = ttk.Frame(canvas)
        
        self.scrollable_progress_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_progress_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 关闭按钮
        close_btn = ttk.Button(progress_frame, text="最小化到后台", 
                              command=self.progress_window.withdraw)
        close_btn.pack(pady=(15, 0))
        
        # 初始化进度跟踪
        self.video_progress_bars = {}
        self.video_progress_labels = {}
        
        # 为每个视频创建进度条
        for i, video in enumerate(self.selected_videos):
            video_id = video.get('id', f'video_{i+1}')
            video_frame = ttk.Frame(self.scrollable_progress_frame)
            video_frame.pack(fill="x", pady=5)
            
            ttk.Label(video_frame, text=f"视频 {video_id}:", width=15, anchor="w").pack(side="left")
            
            progress_bar = ttk.Progressbar(video_frame, length=200, mode='determinate')
            progress_bar.pack(side="left", padx=(10, 5))
            
            progress_label = ttk.Label(video_frame, text="0%", width=8, anchor="w")
            progress_label.pack(side="left")
            
            self.video_progress_bars[video_id] = progress_bar
            self.video_progress_labels[video_id] = progress_label
    
    def download_videos_thread(self):
        try:
            downloaded_count = 0
            total_videos = len(self.selected_videos)
            
            # 更新总进度
            self.root.after(0, lambda: self.update_total_progress(0, total_videos))
            
            # 使用线程池并发下载，最大并发数设为3
            max_workers = 3
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有下载任务
                future_to_video = {
                    executor.submit(self.download_single_video, video, i, total_videos): (video, i)
                    for i, video in enumerate(self.selected_videos)
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_video):
                    video, index = future_to_video[future]
                    try:
                        result = future.result()
                        if result:
                            downloaded_count += 1
                            self.log_message(f"视频下载成功: {result}")
                        else:
                            self.log_message(f"视频下载失败: {video.get('id', 'N/A')}")
                    except Exception as e:
                        video_id = video.get('id', 'N/A')
                        self.log_message(f"下载视频 {video_id} 时出错: {str(e)}")
                    
                    # 更新总进度
                    self.root.after(0, lambda current=downloaded_count, total=total_videos: 
                        self.update_total_progress(current, total))
            
            # 下载完成
            self.root.after(0, lambda: self.download_complete(downloaded_count))
            
        except Exception as e:
            error_msg = f"下载出错: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: self.status_label.config(text=error_msg))
            self.root.after(0, lambda: self.download_btn.config(state="normal"))
            # 关闭进度窗口
            self.root.after(0, lambda: self.close_progress_window())

    def download_single_video(self, video, index, total_videos):
        """下载单个视频"""
        try:
            video_id = video.get('id', 'N/A')
            self.log_message(f"正在下载 ({index+1}/{total_videos}): 视频ID {video_id}")
            
            # 更新状态栏
            self.root.after(0, lambda idx=index, total=total_videos, vid=video_id: 
                self.status_label.config(text=f"正在下载 ({idx+1}/{total}): 视频ID {vid}"))
            
            # 寻找高质量视频文件
            video_files = video.get("video_files", [])
            best_video_url = None
            best_quality = 0
            
            # 寻找最高质量的视频
            for file in video_files:
                width = file.get("width", 0)
                height = file.get("height", 0)
                quality = width * height
                
                # 优先选择4K或更高分辨率的视频
                if quality >= 8294400:  # 3840 * 2160 (4K)
                    best_video_url = file.get("link")
                    break
                elif quality > best_quality:
                    best_quality = quality
                    best_video_url = file.get("link")
            
            if not best_video_url:
                # 如果没有找到合适的链接，尝试使用第一个视频文件
                if video_files:
                    best_video_url = video_files[0].get("link")
                    self.log_message(f"警告: 视频 {video_id} 没有4K版本，使用可用的最高质量版本")
                else:
                    error_msg = f"视频 {video_id} 没有可用的下载链接"
                    self.log_message(error_msg)
                    # 更新进度为100%表示失败
                    self.root.after(0, lambda vid=video_id: self.update_video_progress(vid, 100, "失败"))
                    return None
            
            # 下载视频
            filename = f"pexels_video_{video_id}.mp4"
            filepath = self.download_dir / filename
            
            self.log_message(f"开始下载: {filename}")
            
            # 添加User-Agent避免被拒绝
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Authorization': self.api_key
            }
            
            response = requests.get(best_video_url, stream=True, timeout=120, headers=headers)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # 更新进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            # 在UI线程中更新进度
                            self.root.after(0, lambda vid=video_id, p=progress: 
                                self.update_video_progress(vid, p, f"{p:.1f}%"))
            
            self.log_message(f"下载完成: {filename}")
            # 更新进度为100%表示完成
            self.root.after(0, lambda vid=video_id: self.update_video_progress(vid, 100, "完成"))
            
            return filename
            
        except Exception as e:
            video_id = video.get('id', 'N/A')
            self.log_message(f"下载视频 {video_id} 时出错: {str(e)}")
            # 更新进度为100%表示失败
            self.root.after(0, lambda vid=video_id: self.update_video_progress(vid, 100, "失败"))
            return None
    
    def update_video_progress(self, video_id, progress, label_text):
        """更新单个视频的下载进度"""
        try:
            if hasattr(self, 'video_progress_bars') and video_id in self.video_progress_bars:
                self.video_progress_bars[video_id].config(value=progress)
                self.video_progress_labels[video_id].config(text=label_text)
        except Exception as e:
            pass  # 忽略进度更新错误
    
    def update_total_progress(self, current, total):
        """更新总下载进度"""
        try:
            if hasattr(self, 'total_progress'):
                progress = (current / total * 100) if total > 0 else 0
                self.total_progress.config(value=progress)
                self.total_progress_label.config(text=f"{current}/{total}")
        except Exception as e:
            pass  # 忽略进度更新错误
    
    def close_progress_window(self):
        """关闭进度窗口"""
        try:
            if hasattr(self, 'progress_window') and self.progress_window:
                self.progress_window.destroy()
                self.progress_window = None
        except Exception as e:
            pass
    
    def download_complete(self, count):
        completion_msg = f"下载完成! 成功下载 {count} 个视频到: {self.download_dir}"
        self.status_label.config(text=completion_msg)
        self.log_message(completion_msg)
        self.download_btn.config(state="normal", text="下载选中视频")
        
        # 重新启用选中的复选框
        for video in self.selected_videos:
            var = video.get("selection_var")
            if var:
                var.set(False)
        self.selected_videos = []
        
        # 关闭进度窗口
        self.root.after(2000, lambda: self.close_progress_window())
        
        # 显示下载完成消息框
        messagebox.showinfo("下载完成", f"成功下载 {count} 个视频!\n保存位置: {self.download_dir}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PexelsVideoDownloader()
    app.run()