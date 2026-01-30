import requests
import json
import os
from datetime import datetime
import time

# ==========================================
# 配置区域 - 这里不需要改，通过Secrets传入
# ==========================================
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")  # 飞书机器人地址
TIANAPI_KEY = os.getenv("TIANAPI_KEY")        # 天行API密钥（可选）

class TrendingBot:
    def __init__(self):
        # 模拟浏览器访问，避免被反爬虫拦截
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.zhihu.com/"
        })
        self.results = {}
    
    def fetch_zhihu(self):
        """抓取知乎热榜 - 使用官方API（无需登录）"""
        try:
            print("🚀 开始抓取知乎热榜...")
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20"
            
            resp = self.session.get(url, timeout=15)
            
            # 检查是否被反爬
            if resp.status_code == 403:
                print("❌ 知乎返回403，可能被反爬，尝试更换IP或稍后重试")
                return False
            
            data = resp.json()
            hot_list = []
            
            for item in data.get("data", [])[:15]:  # 只取前15条
                target = item.get("target", {})
                hot_list.append({
                    "title": target.get("title", "无标题"),
                    "url": target.get("url", ""),
                    "hot": item.get("detail_text", "").replace("万热度", "w"),
                    "rank": len(hot_list) + 1
                })
            
            self.results["知乎"] = hot_list
            print(f"✅ 知乎：成功获取 {len(hot_list)} 条")
            return True
            
        except Exception as e:
            print(f"❌ 知乎抓取失败：{str(e)}")
            # 出错时添加空数据，避免整个程序崩溃
            self.results["知乎"] = [{"title": "获取失败", "url": "", "hot": "", "rank": 1}]
            return False
    
    def fetch_weibo(self):
        """
        抓取微博热搜 - 优先使用天行API（稳定），否则使用备用方案
        天行API注册：https://www.tianapi.com/apiview/100
        """
        try:
            print("🚀 开始抓取微博热搜...")
            
            # 方案1：如果配置了天行API，使用它（更稳定）
            if TIANAPI_KEY:
                url = f"https://apis.tianapi.com/networkhot/index?key={TIANAPI_KEY}"
                resp = self.session.get(url, timeout=10)
                data = resp.json()
                
                if data.get("code") == 200:
                    hot_list = []
                    for item in data.get("result", {}).get("list", [])[:15]:
                        hot_list.append({
                            "title": item.get("hotword", ""),
                            "url": "",  # 天行API不返回链接，需手动搜索
                            "hot": str(item.get("hotwordnum", "")),
                            "rank": len(hot_list) + 1
                        })
                    self.results["微博"] = hot_list
                    print(f"✅ 微博（天行API）：成功获取 {len(hot_list)} 条")
                    return True
                else:
                    print(f"⚠️ 天行API返回错误：{data.get('msg')}")
            
            # 方案2：使用第三方免费API（稳定性一般，可能随时失效）
            # 如果天行API失败或未配置，尝试备用接口
            print("⚠️ 尝试备用接口...")
            backup_url = "https://api.vvhan.com/api/hotlist/wbHot"
            resp = self.session.get(backup_url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    hot_list = []
                    for item in data.get("data", [])[:15]:
                        hot_list.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "hot": item.get("hot", ""),
                            "rank": len(hot_list) + 1
                        })
                    self.results["微博"] = hot_list
                    print(f"✅ 微博（备用）：成功获取 {len(hot_list)} 条")
                    return True
            
            # 如果都失败了
            self.results["微博"] = [{"title": "微博获取失败，请检查API配置", "url": "", "hot": "", "rank": 1}]
            return False
            
        except Exception as e:
            print(f"❌ 微博抓取失败：{str(e)}")
            self.results["微博"] = [{"title": "获取失败", "url": "", "hot": "", "rank": 1}]
            return False
    
    def fetch_v2ex(self):
        """抓取V2EX热帖 - 官方API，相对稳定"""
        try:
            print("🚀 开始抓取V2EX热帖...")
            url = "https://www.v2ex.com/api/topics/hot.json"
            
            resp = self.session.get(url, timeout=10)
            
            # V2EX有反爬，如果失败等一下再试
            if resp.status_code != 200:
                print(f"⚠️ V2EX返回状态码：{resp.status_code}，等待2秒后重试...")
                time.sleep(2)
                resp = self.session.get(url, timeout=10)
            
            data = resp.json()
            hot_list = []
            
            for item in data[:10]:  # V2EX取前10条
                hot_list.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "hot": f"💬 {item.get('replies', 0)}",
                    "rank": len(hot_list) + 1
                })
            
            self.results["V2EX"] = hot_list
            print(f"✅ V2EX：成功获取 {len(hot_list)} 条")
            return True
            
        except Exception as e:
            print(f"❌ V2EX抓取失败：{str(e)}")
            self.results["V2EX"] = [{"title": "获取失败", "url": "", "hot": "", "rank": 1}]
            return False
    
    def generate_message(self):
        """生成飞书消息格式"""
        now = datetime.now().strftime("%m月%d日 %H:%M")
        
        # 构建Markdown内容
        content = f"### 🔥 全网热点监控 - {now}\n\n"
        
        # 知乎部分
        content += "**📖 知乎热榜**\n"
        if "知乎" in self.results and self.results["知乎"]:
            for item in self.results["知乎"][:10]:  # 只展示前10
                emoji = "🔥" if item['rank'] <= 3 else "•"
                title = item['title'][:25] + '...' if len(item['title']) > 25 else item['title']
                hot = f" ({item['hot']})" if item['hot'] else ""
                content += f"{emoji} {item['rank']}. [{title}]({item['url']}){hot}\n"
        else:
            content += "获取失败\n"
        
        content += "\n**🎤 微博热搜**\n"
        if "微博" in self.results and self.results["微博"]:
            for item in self.results["微博"][:10]:
                emoji = "🔥" if item['rank'] <= 3 else "•"
                title = item['title'][:25] + '...' if len(item['title']) > 25 else item['title']
                hot = f" ({item['hot']})" if item['hot'] else ""
                content += f"{emoji} {item['rank']}. {title}{hot}\n"
        else:
            content += "获取失败\n"
        
        content += "\n**💻 V2EX热帖**\n"
        if "V2EX" in self.results and self.results["V2EX"]:
            for item in self.results["V2EX"][:8]:
                title = item['title'][:22] + '...' if len(item['title']) > 22 else item['title']
                content += f"• [{title}]({item['url']}) {item['hot']}\n"
        else:
            content += "获取失败\n"
        
        # 构建飞书卡片消息
        card_message = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 每小时热点汇总 | {now}"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    },
                    {
                        "tag": "hr"  # 分割线
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": "💡 由 GitHub Actions 自动推送 | 如有问题请检查Actions日志"
                            }
                        ]
                    }
                ]
            }
        }
        
        return card_message
    
    def send_feishu(self):
        """发送到飞书"""
        if not FEISHU_WEBHOOK:
            print("\n" + "="*50)
            print("⚠️ 警告：未检测到飞书Webhook地址")
            print("本地测试模式：仅打印消息内容，不实际发送")
            print("="*50 + "\n")
            print(json.dumps(self.generate_message(), ensure_ascii=False, indent=2))
            return False
        
        try:
            message = self.generate_message()
            print("📤 正在发送飞书消息...")
            
            resp = requests.post(
                FEISHU_WEBHOOK, 
                json=message, 
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            result = resp.json()
            
            if result.get("code") == 0:
                print("✅ 飞书推送成功！")
                return True
            else:
                print(f"❌ 飞书推送失败：{result.get('msg')}")
                return False
                
        except Exception as e:
            print(f"❌ 发送飞书消息时出错：{str(e)}")
            return False
    
    def run(self):
        """主运行流程"""
        print(f"\n{'='*50}")
        print(f"🤖 热点监控机器人启动 - {datetime.now()}")
        print(f"{'='*50}\n")
        
        # 依次抓取三个平台（带延迟，避免请求过快被拉黑）
        self.fetch_zhihu()
        time.sleep(2)  # 等待2秒
        
        self.fetch_weibo()
        time.sleep(2)
        
        self.fetch_v2ex()
        
        print(f"\n{'='*50}")
        print("📊 抓取结果统计：")
        for platform, items in self.results.items():
            print(f"  {platform}: {len(items)} 条")
        print(f"{'='*50}\n")
        
        # 发送消息
        self.send_feishu()
        
        print(f"\n🏁 任务完成 - {datetime.now()}\n")

# ==========================================
# 程序入口
# ==========================================
if __name__ == "__main__":
    bot = TrendingBot()
    bot.run()
