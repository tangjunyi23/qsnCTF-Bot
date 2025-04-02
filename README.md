# Saki酱 - 基于Nonebot的AI聊天机器人

Saki酱是一个基于 [Nonebot2](https://github.com/nonebot/nonebot2) 开发的智能聊天机器人，集成了 DeepSeek AI 及 通义千问视觉模型，可进行智能对话、图片分析、群聊互动等。

## ✨ 主要功能

- **智能对话**：基于 DeepSeek AI 提供精准、流畅的聊天体验。
- **图片分析**：使用通义千问视觉模型解析图片内容。
- **群聊互动**：可配置随机回复，让群聊更加活跃。
- **自定义个性**：支持自定义机器人的性格、风格和背景。
- **命令控制**：提供指令管理随机回复、清空对话等。

## 📦 依赖环境

请确保你的环境满足以下要求：

- Python 3.8 及以上
- Nonebot2
- OneBot v11 适配器
- OpenAI SDK
- httpx
- asyncio

## 🚀 安装与运行

### 1. 克隆项目
```bash
git clone https://github.com/your_username/your_repository.git
cd your_repository
```
2. 安装依赖
```
pip install -r requirements.txt
```
3. 配置 API 密钥

在 .env 或 config.py 中填入你的 API 密钥：
```
DEEPSEEK_API_KEY=your_deepseek_api_key
ALIYUN_VISION_API_KEY=your_aliyun_api_key
```
4. 运行机器人
```
nb run
```
🎯 使用指南

主要指令

与Saki酱聊天：
```
@Saki酱 + 消息 进行聊天
```
发送图片，Saki酱会解析图片内容并回复

随机回复控制：
```
set.开启随机回复 开启群聊随机回复

set.关闭随机回复 关闭群聊随机回复
```
清空对话：
```
#clear_context 或 #清空对话 重置对话历史
```
帮助指令：
```
#help 或 #指令 查看支持的命令
```
🔧 配置说明

你可以在 bot_settings 变量中修改机器人的设定，例如名称、性格、风格等。
```
bot_settings = {
    "name": "Saki酱",
    "personality": "温柔，有时候大大咧咧",
    "style": "可爱俏皮",
    "background": "16岁女高中生，喜欢网上冲浪，懂得很多网络流行语，喜欢二次元，喜欢看动画，喜欢玩游戏，喜欢聊天。"
}
```
🤝 贡献指南

欢迎提交 issue 和 PR，贡献你的想法和代码！

Fork 代码

创建新分支 (git checkout -b feature-xxx)

提交代码 (git commit -m '新增xxx功能')

Push 到你的分支 (git push origin feature-xxx)

提交 PR


   
# CTF信息查询插件

一个基于 [NoneBot2](https://github.com/nonebot/nonebot2) 的插件，用于查询青少年CTF平台的赛事信息、排行榜、解题动态等内容。

## 功能介绍

- **赛事查询**：获取近期CTF赛事的详细信息。
- **排行榜**：查看指定页码的排行榜信息。
- **解题动态**：获取最新的解题动态。
- **用户查询**：查询指定用户的详细信息。
- **凭据更新**：自动登录并更新凭据，确保API请求正常运行。

## 安装方法

1. 确保已安装 [NoneBot2](https://github.com/nonebot/nonebot2) 和 `onebot-adapter-v11`。
2. 克隆本仓库到您的 NoneBot 插件目录：
   ```bash
   git clone https://github.com/your-username/liyuu.git
