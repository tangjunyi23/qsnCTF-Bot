from nonebot import on_command, on_message, require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message, MessageSegment
from nonebot.typing import T_State
from nonebot.log import logger
from nonebot.rule import to_me, Rule  # 导入规则相关模块
from nonebot.plugin import PluginMetadata  # 导入插件元数据
from nonebot.permission import Permission
from nonebot.matcher import Matcher
import requests
import json
import os
import asyncio
import base64
from datetime import datetime
from pathlib import Path
import time
import re

# 插件元数据定义
__plugin_meta__ = PluginMetadata(
    name="CTF信息查询",
    description="查询CTF赛事、排行榜、解题动态等信息",
    usage="ctf.help - 查看帮助\nctf.赛事 - 查看近期赛事\nctf.排行 - 查看排行榜\nctf.动态 - 查看解题动态\nctf.信息 - 查看个人信息\nctf.更新凭据 - 更新登录凭据",
    type="application",
    homepage="https://github.com/your-username/liyuu",
    config=None,
    supported_adapters={"~onebot.v11"},
)

# Selenium相关导入
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 命令前缀和命令名称
CMD_PREFIX = "ctf"
HELP_CMD = f"{CMD_PREFIX}.help"
LIST_CMD = f"{CMD_PREFIX}.赛事"
RANK_CMD = f"{CMD_PREFIX}.排行"
DYNAMIC_CMD = f"{CMD_PREFIX}.动态"
INFO_CMD = f"{CMD_PREFIX}.信息"
UPDATE_CMD = f"{CMD_PREFIX}.更新凭据"
QUERY_CMD = f"{CMD_PREFIX}.查询"

# API基础URL
BASE_URL = "https://www.qsnctf.com/api"

# 插件数据目录
DATA_DIR = Path(__file__).parent
CREDENTIALS_PATH = DATA_DIR / "credentials.json"

# 凭据信息和过期时间
credentials = None
credentials_expiry = 0

# 创建一个匹配CTF命令的规则，不需要@
def ctf_command_pattern() -> Rule:
    async def _checker(event: Event) -> bool:
        if isinstance(event, GroupMessageEvent):
            msg_text = event.get_plaintext().strip()
            return msg_text.startswith(f"{CMD_PREFIX}.")
        return False
    return Rule(_checker)

# 自定义匹配规则 - 检查消息是否以CTF命令开头，不需要@
def ctf_command_rule(cmd_str: str) -> Rule:
    async def _checker(event: Event) -> bool:
        if isinstance(event, GroupMessageEvent):
            msg_text = event.get_plaintext().strip()
            return msg_text == cmd_str
        return False
    return Rule(_checker)

# 自定义规则检查器 - 支持多个命令前缀，不需要@
def rule_matcher(cmd_prefixes: list) -> Rule:
    async def _checker(event: Event) -> bool:
        if isinstance(event, GroupMessageEvent):
            msg_text = event.get_plaintext().strip()
            for prefix in cmd_prefixes:
                if msg_text.startswith(prefix):
                    return True
        return False
    return Rule(_checker)

# 重新定义命令处理器 - 移除to_me()要求
ctf_help = on_command(HELP_CMD, aliases={HELP_CMD}, priority=1, block=True)
ctf_list = on_command(LIST_CMD, aliases={LIST_CMD}, priority=1, block=True)
ctf_rank = on_message(rule=rule_matcher([RANK_CMD]), priority=1, block=True)
ctf_dynamic = on_command(DYNAMIC_CMD, aliases={DYNAMIC_CMD}, priority=1, block=True)
ctf_info = on_command(INFO_CMD, aliases={INFO_CMD}, priority=1, block=True)
ctf_update = on_command(UPDATE_CMD, aliases={UPDATE_CMD}, priority=1, block=True)
ctf_user = on_message(rule=rule_matcher([QUERY_CMD]), priority=1, block=True)

# 创建一个通用的CTF消息处理器 - 处理所有CTF相关消息
ctf_general = on_message(rule=ctf_command_pattern(), priority=1, block=True)

# 启动时加载凭据
@get_driver().on_startup
async def load_credentials_on_startup():
    global credentials, credentials_expiry
    credentials, credentials_expiry = await load_credentials()
    logger.info(f"CTF插件启动: 凭据已加载，过期时间: {datetime.fromtimestamp(credentials_expiry)}")

async def load_credentials():
    """加载凭据及其过期时间"""
    try:
        if CREDENTIALS_PATH.exists():
            with open(CREDENTIALS_PATH, "r") as f:
                creds = json.load(f)
                
                # 从JWT令牌中解析过期时间
                auth_token = creds["Authorization"].split("Bearer ")[-1]
                token_parts = auth_token.split('.')
                if len(token_parts) == 3:
                    try:
                        # 解码JWT负载部分
                        payload = token_parts[1]
                        # 确保正确的padding
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        payload_data = json.loads(decoded)
                        
                        # 提取过期时间
                        if 'exp' in payload_data:
                            return creds, payload_data['exp']
                    except Exception as e:
                        logger.error(f"解析JWT令牌时出错: {e}")
                
                # 如果无法解析令牌，使用默认过期时间（24小时后）
                return creds, time.time() + 86400
            
        logger.warning("凭据文件不存在，需要登录获取")
        return None, 0
    except Exception as e:
        logger.error(f"加载凭据时出错: {e}")
        return None, 0

async def ensure_valid_credentials():
    """确保凭据有效，必要时更新"""
    global credentials, credentials_expiry
    
    if not credentials:
        logger.error("没有可用的凭据")
        return False
        
    current_time = time.time()
    # 如果凭据将在10分钟内过期
    if current_time > (credentials_expiry - 600):
        logger.warning("凭据即将过期，需要更新")
        return False
    
    return True

def get_headers():
    """返回带认证的标准请求头"""
    if not credentials:
        return None
        
    return {
        "Authorization": credentials["Authorization"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }

# 通用处理器 - 处理所有CTF相关命令
@ctf_general.handle()
async def handle_ctf_command(bot: Bot, event: Event):
    msg_text = event.get_plaintext().strip()
    logger.info(f"接收到CTF命令: {msg_text} 来自: {event.get_user_id()}")
    
    if HELP_CMD in msg_text or "帮助" in msg_text:
        await handle_help(bot, event)
    elif LIST_CMD in msg_text or "赛事" in msg_text:
        await handle_list(bot, event)
    elif RANK_CMD in msg_text or "排行" in msg_text:
        await handle_rank(bot, event)
    elif DYNAMIC_CMD in msg_text or "动态" in msg_text:
        await handle_dynamic(bot, event)
    elif INFO_CMD in msg_text or "信息" in msg_text:
        await handle_info(bot, event)
    elif UPDATE_CMD in msg_text or "更新凭据" in msg_text:
        await handle_update(bot, event)
    elif QUERY_CMD in msg_text or "查询" in msg_text:
        await handle_user_query(bot, event)
    else:
        await bot.send(event, f"未知CTF命令: {msg_text}\n请使用 ctf.help 查看帮助")

@ctf_update.handle()
async def handle_update(bot: Bot, event: Event):
    """自动更新登录凭据"""
    logger.info(f"接收到更新凭据请求: {event.get_user_id()}")
    await bot.send(event, "开始更新QSNCTF登录凭据，请在60秒内完成登录操作...")
    
    # 异步执行登录操作
    success = await asyncio.to_thread(login_and_update_credentials)
    
    if success:
        # 重新加载凭据
        global credentials, credentials_expiry
        credentials, credentials_expiry = await load_credentials()
        await bot.send(event, f"✅ 凭据更新成功！新的过期时间: {datetime.fromtimestamp(credentials_expiry)}")
    else:
        await bot.send(event, "❌ 凭据更新失败，请稍后重试")

def login_and_update_credentials():
    """执行自动登录并获取凭据"""
    # 配置Chrome选项以启用性能日志
    chrome_options = Options()
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 创建Chrome浏览器实例
    browser = webdriver.Chrome(options=chrome_options)

    try:
        # 打开登录页面
        browser.get('https://www.qsnctf.com/#/login')

        # 等待页面跳转到目标地址
        target_url = 'https://www.qsnctf.com/#/main/driving-range'
        WebDriverWait(browser, 60).until(EC.url_to_be(target_url))
        logger.info("检测到登录成功")

        # 等待可能的API请求完成
        time.sleep(3)

        # 获取性能日志并查找Authorization头
        logs = browser.get_log('performance')
        authorization = None

        for entry in logs:
            try:
                log = json.loads(entry['message'])
                message = log.get('message', {})

                # 检查网络请求事件
                if message.get('method') in ['Network.requestWillBeSentExtraInfo', 'Network.requestWillBeSent']:
                    headers = message.get('params', {}).get('headers', {})
                    if headers and 'authorization' in headers:
                        auth_header = headers['authorization']
                        authorization = auth_header
                        logger.info("成功获取Authorization")
                        break

            except Exception as e:
                logger.error(f"解析日志时出错: {e}")
                continue

        # 获取Cookies
        cookies = browser.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        logger.info("成功获取Cookie")

        # 保存到credentials.json
        if authorization:
            headers = {
                "Authorization": authorization,
                "Cookies": cookie_dict
            }
            with open(CREDENTIALS_PATH, 'w') as f:
                json.dump(headers, f, indent=4)
            logger.info(f"凭据已保存到 {CREDENTIALS_PATH}")
            browser.quit()
            return True
        else:
            logger.error("未找到Authorization，更新凭据失败")
            browser.quit()
            return False

    except Exception as e:
        logger.error(f"登录过程中出错: {e}")
        try:
            browser.quit()
        except:
            pass
        return False

# 命令处理函数 - 更新帮助文本，移除@要求
async def handle_help(bot: Bot, event: Event):
    logger.info(f"处理help请求: {event.get_user_id()}")
    help_text = (
        "青少年CTF平台查询小助手！！！ v1.1\n"
        "支持命令：\n"
        f"{CMD_PREFIX}.赛事 - 查看近期赛事列表\n"
        f"{CMD_PREFIX}.排行 [页码] - 查看排行榜，可指定页码\n"
        f"{CMD_PREFIX}.动态 - 查看解题动态\n"
        f"{CMD_PREFIX}.信息 - 查看个人账号信息\n"
        f"{CMD_PREFIX}.查询 用户名 - 查询指定用户信息\n"
        f"{CMD_PREFIX}.更新凭据 - 手动更新登录凭据"
    )
    await bot.send(event, help_text)

async def handle_list(bot: Bot, event: Event):
    logger.info(f"处理赛事请求: {event.get_user_id()}")
    await bot.send(event, "正在获取最新赛事信息...")
    result = await get_game_list()
    await bot.send(event, result)

@ctf_rank.handle()
async def handle_rank(bot: Bot, event: Event):
    logger.info(f"处理排行请求: {event.get_user_id()}")
    
    # 解析命令，检查是否包含页码参数
    command_text = event.get_plaintext()
    page = 1  # 默认第一页
    
    # 尝试提取页码参数
    match = re.search(r'排行\s+(\d+)', command_text)
    if match:
        page = int(match.group(1))
    
    await bot.send(event, f"正在获取排行榜第{page}页...")
    result = await get_leaderboard(page)
    await bot.send(event, result)

async def handle_dynamic(bot: Bot, event: Event):
    logger.info(f"处理动态请求: {event.get_user_id()}")
    await bot.send(event, "正在获取解题动态...")
    result = await get_dynamic()
    await bot.send(event, result)

async def handle_info(bot: Bot, event: Event):
    logger.info(f"处理信息请求: {event.get_user_id()}")
    await bot.send(event, "正在获取个人信息...")
    result = await get_user_info()
    await bot.send(event, result)

@ctf_user.handle()
async def handle_user_query(bot: Bot, event: Event):
    logger.info(f"处理用户查询请求: {event.get_user_id()}")
    
    # 解析命令，提取用户名
    command_text = event.get_plaintext()
    match = re.search(r'查询\s+(.+)', command_text)
    
    if match:
        username = match.group(1).strip()
        await bot.send(event, f"正在查询用户 {username} 的信息...")
        result = await search_user(username)
        await bot.send(event, result)
    else:
        await bot.send(event, "请指定要查询的用户名，例如：ctf.查询 用户名")

# 异步获取数据函数 - 简化错误输出
async def get_game_list():
    """获取并格式化赛事列表"""
    if not await ensure_valid_credentials():
        return "❌ 凭据无效或已过期，请使用 ctf.更新凭据 命令更新"
    
    try:
        game_data = await asyncio.to_thread(
            fetch_game_list,
            1,  # 默认获取第1页
            5   # 每页显示5条
        )
        
        if not game_data or "results" not in game_data:
            return "获取赛事列表失败，请稍后再试"
        
        # 格式化赛事列表
        return format_game_list(game_data.get("results", []))
    
    except Exception as e:
        logger.error(f"获取赛事列表出错: {e}")
        return "获取赛事列表失败 (错误码: 500)"

async def get_leaderboard(page=1, page_size=10):
    """获取并格式化排行榜，支持分页"""
    if not await ensure_valid_credentials():
        return "❌ 凭据无效或已过期，请使用 ctf.更新凭据 命令更新"
    
    try:
        race_id = await asyncio.to_thread(get_practice_race_id)
        if not race_id:
            return "获取竞赛ID失败，请稍后再试"
        
        rank_data = await asyncio.to_thread(
            fetch_leaderboard,
            race_id,
            page,  # 使用指定的页码
            page_size  # 每页显示数量
        )
        
        if not rank_data or "results" not in rank_data:
            return "获取排行榜失败，请稍后再试"
        
        # 获取总页数信息
        total_count = rank_data.get("count", 0)
        total_pages = (total_count + page_size - 1) // page_size
        
        # 格式化排行榜，并加入分页信息
        formatted_ranks = format_leaderboard(rank_data.get("results", []), page, page_size)
        return f"📊 排行榜 (第{page}/{total_pages}页, 共{total_count}人)\n{formatted_ranks}"
        
    except Exception as e:
        logger.error(f"获取排行榜出错: {e}")
        return "获取排行榜失败 (错误码: 500)"

async def get_dynamic():
    """获取并格式化解题动态"""
    if not await ensure_valid_credentials():
        return "❌ 凭据无效或已过期，请使用 ctf.更新凭据 命令更新"
    
    try:
        race_id = await asyncio.to_thread(get_practice_race_id)
        if not race_id:
            return "获取竞赛ID失败，请稍后再试"
        
        dynamic_data = await asyncio.to_thread(
            fetch_dynamic,
            race_id
        )
        
        if not dynamic_data or "results" not in dynamic_data:
            return "获取解题动态失败，请稍后再试"
        
        return format_dynamic(dynamic_data.get("results", []))
        
    except Exception as e:
        logger.error(f"获取解题动态出错: {e}")
        return "获取解题动态失败 (错误码: 500)"

async def get_user_info():
    """获取并格式化用户信息"""
    if not await ensure_valid_credentials():
        return "❌ 凭据无效或已过期，请使用 ctf.更新凭据 命令更新"
    
    try:
        user_data = await asyncio.to_thread(fetch_user_info)
        if not user_data:
            return "获取个人信息失败，请稍后再试"
        
        return format_user_info(user_data)
        
    except Exception as e:
        logger.error(f"获取个人信息出错: {e}")
        return "获取个人信息失败 (错误码: 500)"

async def search_user(username):
    """查询指定用户信息"""
    if not await ensure_valid_credentials():
        return "❌ 凭据无效或已过期，请使用 ctf.更新凭据 命令更新"
    
    try:
        # 获取用户信息
        user_data = await asyncio.to_thread(fetch_user_by_name, username)
        
        if not user_data or "results" not in user_data or not user_data["results"]:
            return f"未找到用户 {username} 的信息"
        
        # 如果有多个用户匹配，取第一个
        user_info = user_data["results"][0]
        
        # 格式化用户信息
        return format_user_detail(user_info)
        
    except Exception as e:
        logger.error(f"查询用户信息出错: {e}")
        return "查询用户信息失败 (错误码: 500)"

# API请求函数
def get_practice_race_id():
    """获取练习场ID"""
    headers = get_headers()
    try:
        response = requests.get(
            f"{BASE_URL}/api/practice_race",
            headers=headers,
            cookies=credentials.get("Cookies", {}),
            timeout=10
        )
        response.raise_for_status()
        race_data = response.json()
        return race_data.get('results', {}).get('id')
    except Exception as e:
        logger.error(f"获取练习场ID出错: {e}")
        return None

def fetch_game_list(page=1, page_size=5):
    """获取赛事列表"""
    headers = get_headers()
    response = requests.get(
        f"{BASE_URL}/api/races?page={page}&page_size={page_size}&competition_format=&race_tag=&keyword=",
        headers=headers,
        cookies=credentials.get("Cookies", {}),
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def fetch_leaderboard(race_id, page=1, page_size=10):
    """获取排行榜"""
    headers = get_headers()
    response = requests.get(
        f"{BASE_URL}/api/races/{race_id}/score_leaderboard?page={page}&page_size={page_size}",
        headers=headers,
        cookies=credentials.get("Cookies", {}),
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def fetch_dynamic(race_id, page=1, page_size=10):
    """获取解题动态"""
    headers = get_headers()
    response = requests.get(
        f"{BASE_URL}/api/races/{race_id}/dynamic?page={page}&page_size={page_size}",
        headers=headers,
        cookies=credentials.get("Cookies", {}),
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def fetch_user_info():
    """获取用户信息"""
    headers = get_headers()
    response = requests.get(
        f"{BASE_URL}/profile",
        headers=headers,
        cookies=credentials.get("Cookies", {}),
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def fetch_user_by_name(username):
    """根据用户名查询用户"""
    headers = get_headers()
    try:
        response = requests.get(
            f"{BASE_URL}/api/users?search={username}",
            headers=headers,
            cookies=credentials.get("Cookies", {}),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"获取用户信息出错: {e}")
        return None

# 格式化函数
def format_game_list(games):
    """格式化赛事列表"""
    if not games:
        return "暂无赛事信息"
    
    result = "🏆 CTF赛事列表\n"
    result += "━━━━━━━━━━━━━━\n"
    
    for game in games:
        title = game.get("title", "未知赛事")
        org = game.get("organizing_institution", "未知组织方")
        start = format_time(game.get("enroll_start_time", ""))
        end = format_time(game.get("enroll_end_time", ""))
        race_start = format_time(game.get("race_start_time", ""))
        race_end = format_time(game.get("race_end_time", ""))
        
        result += f"📌 {title}\n"
        result += f"主办方: {org}\n"
        result += f"报名时间: {start} 至 {end}\n"
        result += f"比赛时间: {race_start} 至 {race_end}\n"
        result += "━━━━━━━━━━━━━━\n"
    
    return result

def format_leaderboard(ranks, page=1, page_size=10):
    """格式化排行榜"""
    if not ranks:
        return "暂无排行榜信息"
    
    result = "🏆 CTF排行榜\n"
    result += "━━━━━━━━━━━━━━\n"
    
    start_rank = (page - 1) * page_size + 1
    for idx, rank in enumerate(ranks, start_rank):
        name = rank.get("name", "未知用户")
        score = rank.get("score", 0)
        count = rank.get("count", 0)
        category = rank.get("category_name", "未知")
        
        result += f"{idx}. {name}\n"
        result += f"   积分: {score} | 解题: {count} | 擅长: {category}\n"
    
    result += "━━━━━━━━━━━━━━\n"
    return result

def format_dynamic(dynamics):
    """格式化解题动态"""
    if not dynamics:
        return "暂无解题动态"
    
    result = "📊 最新解题动态\n"
    result += "━━━━━━━━━━━━━━\n"
    
    for dynamic in dynamics[:5]:  # 只显示最新的5条
        username = dynamic.get("username", "未知用户")
        challenge = dynamic.get("ctf_challenge", "未知题目")
        time = format_time(dynamic.get("create_time", ""))
        
        result += f"👤 {username} 解决了 {challenge}\n"
        result += f"⏰ {time}\n"
        result += "━━━━━━━━━━━━━━\n"
    
    return result

def format_user_info(user_data):
    """格式化用户信息"""
    if not user_data:
        return "暂无用户信息"
    
    username = user_data.get("username", "未知")
    points = user_data.get("points_numbers", 0)
    gold = user_data.get("gold_coins", 0)
    email = user_data.get("email", "未设置")
    phone = user_data.get("phone", "未设置")
    
    result = "🔍 个人账号信息\n"
    result += "━━━━━━━━━━━━━━\n"
    result += f"👤 用户名: {username}\n"
    result += f"📊 积分: {points}\n"
    result += f"💰 金币: {gold}\n"
    result += f"📧 邮箱: {email}\n"
    result += f"📱 手机: {phone}\n"
    result += "━━━━━━━━━━━━━━\n"
    
    return result

def format_user_detail(user_info):
    """格式化用户详细信息"""
    if not user_info:
        return "暂无用户信息"
    
    username = user_info.get("username", "未知")
    bio = user_info.get("introduction", "无个人介绍")
    points = user_info.get("points_numbers", 0)
    solved = user_info.get("ctf_challenge_numbers", 0)
    rank = user_info.get("rank", 0)
    team = user_info.get("team_name", "无队伍")
    
    result = "🔍 用户信息查询\n"
    result += "━━━━━━━━━━━━━━\n"
    result += f"👤 用户名: {username}\n"
    result += f"📈 积分: {points}\n"
    result += f"🏆 排名: {rank}\n"
    result += f"🎯 解题数: {solved}\n"
    result += f"🚩 队伍: {team}\n"
    result += f"📝 简介: {bio}\n"
    result += "━━━━━━━━━━━━━━\n"
    
    return result

def format_time(time_str):
    """格式化时间字符串"""
    if not time_str:
        return "未知时间"
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return time_str
