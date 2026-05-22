import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import Optional, List
from google import genai
from google.genai import types

# ==================== 1. 定义预期的结构化 JSON 格式 ====================
class AcademicEvent(BaseModel):
    category: str = Field(description="分类，严格限制为：舞剧开票、学术讲座、期刊征稿、赛事通知、其他")
    title: str = Field(description="活动、舞剧或讲座的具体完整名称")
    date_time: Optional[str] = Field(description="核心时间，如讲座时间、开票时间或截稿日期")
    location: Optional[str] = Field(description="地点（线上活动写明平台如腾讯会议及号，线下写明具体场馆或院校）")
    summary: str = Field(description="50字以内的核心内容摘要，提炼关键干货")

class EventList(BaseModel):
    events: List[AcademicEvent] = Field(description="从文章文本和图片中提取出的所有事件列表")

# ==================== 2. 核心处理函数 ====================
def fetch_and_analyze_article(url: str, api_key: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # 绕过本地可能开启的代理软件干扰
    proxies = {"http": None, "https": None}
    
    try:
        # ---- 步骤 A：抓取网页文本 ----
        print("正在下载微信公众号网页...")
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_node = soup.find('div', id='js_content')
        if not content_node:
            return "错误：未能解析到微信正文"
            
        text_content = content_node.get_text(separator="\n", strip=True)
        
        # ---- 步骤 B：初始化大模型输入队列 ----
        prompt = (
            "你是一个专业的艺术学术信息提取助手。请仔细阅读输入的网页文本，并结合附带的所有图片（通常为宣讲海报或演出信息图）。"
            "提取出里面所有的学术讲座、舞剧开票或征稿信息。如果图片海报中的关键信息（如时间、地点）与网页文本不一致，请以图片海报上的准确信息为准。"
        )
        # contents 列表可以同时组合字符串文本和多媒体 Part
        contents = [prompt, f"网页文本内容如下：\n{text_content}"]
        
        # ---- 步骤 C：流式下载图片并转换为字节流 Part ----
        print("正在提取并下载海报图片...")
        img_tags = content_node.find_all('img')
        img_count = 0
        
        for img in img_tags:
            img_url = img.get('data-src')
            if img_url:
                try:
                    img_resp = requests.get(img_url, headers=headers, proxies=proxies, timeout=10)
                    if img_resp.status_code == 200:
                        # 动态获取图片的 Content-Type (例如 image/jpeg, image/png)
                        mime_type = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
                        if "image" in mime_type:
                            # 核心：直接将内存中的图片字节流构造成 Gemini 接受的 Part
                            img_part = types.Part.from_bytes(
                                data=img_resp.content,
                                mime_type=mime_type
                            )
                            contents.append(img_part)
                            img_count += 1
                except Exception:
                    # 单张图片下载失败不中断整个流程
                    continue
                    
        print(f"网页文本分析完毕。已成功加载 {img_count} 张图片输入至大模型。")
        
        # ---- 步骤 D：调用 Gemini API 强制结构化输出 ----
        print("正在请求 Gemini 3.5 API 进行多模态融合分析...")
        client = genai.Client(api_key=api_key)
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json", # 指定返回 JSON
            response_schema=EventList,             # 指定严格遵循 Pydantic 结构
            temperature=0.1                        # 低随机性确保信息准确
        )
        
        response = client.models.generate_content(
            model="gemini-3.5-flash",              # 使用最新多模态速度优势模型
            contents=contents,
            config=config
        )
        
        return response.text

    except Exception as e:
        return f"程序运行异常: {str(e)}"

# ==================== 3. 执行入口 ====================
if __name__ == "__main__":
    # 测试用的微信公众号链接
    test_url = "https://mp.weixin.qq.com/s/a7NfmX_pGPEqXbE3ENsmYw"
    
    # 填入你的真实 Gemini API 密钥
    GEMINI_API_KEY = "AIzaSyCnAV69Pg64cpdVfa7-UnpTzqdF5EGjrMw" 
    
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("请先在代码中配置您的 GEMINI_API_KEY")
    else:
        json_output = fetch_and_analyze_article(test_url, GEMINI_API_KEY)
        print("\n================ Gemini 结构化输出结果 ================")
        print(json_output)
