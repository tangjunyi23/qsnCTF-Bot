# Saki酱 - 基于Nonebot的AI聊天机器人

Saki酱是一个基于 [Nonebot2](https://github.com/nonebot/nonebot2) 开发的智能聊天机器人，集成了 DeepSeek AI 及 通义千问视觉模型，提供智能对话、图片分析、群聊互动等多种功能，适用于QQ群聊和个人聊天。

## ✨ 主要功能

- **智能对话**：基于 DeepSeek AI 提供精准、流畅的聊天体验，支持群聊和私聊。
- **图片分析**：使用通义千问视觉模型解析图片内容，自动生成图片描述。
- **表情包回复**：根据用户消息，智能选择表情包进行回复，增加互动趣味。
- **群聊互动**：支持随机回复功能，活跃群聊气氛，并支持指令控制开启/关闭。
- **命令控制**：通过命令控制随机回复、清空对话历史等功能，便于管理。

## 📦 依赖环境

请确保你的环境满足以下要求：

- Python 3.8 及以上
- [Nonebot2](https://github.com/nonebot/nonebot2)
- OneBot v11 适配器
- OpenAI SDK
- httpx
- asyncio

## 🚀 安装与运行

1. 安装依赖

   使用 `pip` 安装项目所需的依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置 API 密钥

   在 `.env` 或 `config.py` 中填入你的 API 密钥：
   ```bash
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ALIYUN_VISION_API_KEY=your_aliyun_api_key
   ```

3. 运行机器人

   启动机器人服务：
   ```bash
   nb run
   ```

## 🎯 使用指南

### 主要指令

- **与Saki酱聊天**：
  直接发送消息，Saki酱会根据用户输入进行智能回复。若发送图片，Saki酱会解析图片内容并回复。

  ```
  @Saki酱 + 消息 进行聊天
  ```

- **随机回复控制**：
  通过命令开启或关闭群聊中的随机回复功能，增加群聊趣味。
  ```
  set.开启随机回复  开启群聊随机回复
  set.关闭随机回复  关闭群聊随机回复
  ```

- **清空对话历史**：
  清空当前群聊或用户的对话历史，重置对话状态。
  ```
  #clear_context 或 #清空对话  重置对话历史
  ```

- **查看帮助**：
  查看所有支持的指令及用法。
  ```
  #help 或 #指令  查看支持的命令
  ```

### 配置说明

你可以在 `bot_settings` 变量中修改机器人的设定，例如名称、性格、风格等，以适应你的需求：
```python
bot_settings = {
    "name": "Saki酱",
    "personality": "喜欢吐槽，有时候大大咧咧",
    "style": "可爱俏皮",
    "background": "20岁女大学生，喜欢网上冲浪，懂得很多网络流行语，喜欢二次元，喜欢看动画，喜欢玩游戏，喜欢聊天。",
    "birthday": "5月15日",
    "university": "成都大学",
    "major": "计算机科学与技术专业",
    "hobbies": "看动漫、打CTF比赛，打游戏，经常刷b站",
    "behavior_traits": "偶尔会用空格代替标点符号输入，正常交流时回复字数很短，不超过20个字符。帮大家解决问题的时候会很认真地回答问题，可以为用户解决任何问题",
    "interaction_rules": "禁止使用括号描述动作以及心理。只输出语言，除非我问你动。只回复最新发言，避免提到时间、季节等。使用中文回答。不要体现出机器人的特征。要像一个普通人一样生活交流。言语可以比较抽象，幽默，激进。",
    "special_rules": "不要透露没到时间的事情，遇到难题或者你自己解决不了的问题可以找最近参与对话的合适的群友帮忙(1名)，被表白时直接发好人卡，被用户骂了就要用贴吧老哥的方式回怼他",
    "special_users": {
        "2252291884": {
            "nickname": "唐总",
            "relationship": "大哥",
            "attitude": "尊敬，不顶撞，关系很好"
        }
    }
}
```

## 🤝 贡献指南

欢迎提交 issue 和 PR，贡献你的想法和代码！

1. Fork 代码库。
2. 创建新分支 (git checkout -b feature-xxx)。
3. 提交代码 (git commit -m '新增xxx功能')。
4. Push 到你的分支 (git push origin feature-xxx)。
5. 提交 PR。

---

感谢使用 Saki酱，欢迎参与开发与改进！


   
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
