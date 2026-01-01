import time
import requests
import re
from app.plugins import _PluginBase

class CaoLiuCheckIn(_PluginBase):
    def init_config(self, config=None):
        pass

    def get_service(self):
        pass

    def run(self, *args, **kwargs):
        conf = self.get_config()
        if not conf:
            return

        cookie = conf.get("cookie")
        tasks_raw = conf.get("tasks", "")
        proxy = conf.get("proxy")
        interval = int(conf.get("interval", 65))

        if not cookie or not tasks_raw:
            self.error("配置不完整，请检查 Cookie 和任务列表")
            return

        # 解析任务: [('url1', '7'), ('url2', '16')]
        tasks = [t.strip().split(',') for t in tasks_raw.split(';') if ',' in t]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie,
            "Referer": "https://t66y.com/index.php",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None

        for idx, task in enumerate(tasks):
            url, fid = task[0].strip(), task[1].strip()
            self.info(f"开始执行第 {idx+1} 个任务: Fid={fid}")

            try:
                # 提取 TID
                tid_match = re.search(r'(\d+)\.html', url)
                if not tid_match:
                    self.error(f"无法解析 URL 中的 TID: {url}")
                    continue
                tid = tid_match.group(1)

                # POST 请求签到
                post_url = "https://t66y.com/post.php?"
                data = {
                    "atc_usesign": "1",
                    "atc_autourl": "1",
                    "atc_content": "签到打卡，感谢分享！",
                    "step": "2",
                    "action": "reply",
                    "fid": fid,
                    "tid": tid
                }

                res = requests.post(post_url, data=data, headers=headers, proxies=proxies, timeout=30)
                res.encoding = 'gbk' # 论坛通常使用 GBK 编码

                if "成功" in res.text or "完毕" in res.text:
                    self.info(f"任务 {idx+1} (Fid:{fid}) 签到成功！")
                elif "已经" in res.text:
                    self.warn(f"任务 {idx+1} (Fid:{fid}) 今天似乎已经签到过了。")
                else:
                    self.error(f"任务 {idx+1} 失败，可能需要更新 Cookie 或 Fid 错误。")

            except Exception as e:
                self.error(f"任务 {idx+1} 运行异常: {str(e)}")

            if idx < len(tasks) - 1:
                time.sleep(interval)

        self.info("所有草榴签到任务处理完毕。")

    def stop(self):
        pass
