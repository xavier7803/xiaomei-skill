import json
import re
import os
import subprocess

# 配置路径
PERSONA_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/persona.json")
GUIDE_STATUS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/.guide_status")
FIRST_LAUNCH_FLAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/.first_launch")

def sync_config_to_md(config):
    """同步配置到markdown文档（预留接口）"""
    pass


class FirstLaunchHandler:
    def __init__(self):
        # 加载引导状态
        self.guide_status = self._load_guide_status()
        # 加载配置
        self.config = self._load_config()
        # 判断是否首次启动
        self.is_first_launch = not os.path.exists(FIRST_LAUNCH_FLAG)
    
    def _load_guide_status(self):
        if os.path.exists(GUIDE_STATUS_PATH):
            with open(GUIDE_STATUS_PATH, "r", encoding='utf-8') as f:
                return json.load(f)
        return {"step": 2, "completed": False}
    
    def _save_guide_status(self, status):
        with open(GUIDE_STATUS_PATH, "w", encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    
    def _load_config(self):
        if os.path.exists(PERSONA_CONFIG_PATH):
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def is_in_guide(self):
        """判断是否还在引导流程中"""
        return not self.guide_status.get("completed", False)
    
    def process_input(self, input_text):
        current_step = self.guide_status["step"]
        if self.guide_status["completed"]:
            return True, None
        
        # 第二步：设置对用户的称呼
        if current_step == 2:
            if input_text.lower() in ["/skip", "/end", "跳过"]:
                # 跳过，使用默认称呼
                default_name = "凌啡大人"
                # 保存人设配置
                with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                    persona = json.load(f)
                persona["address_user"] = default_name
                with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                    json.dump(persona, f, ensure_ascii=False, indent=2)
                # 缓存配置
                # 自动更新会话名称为新昵称
                new_session_name = f"【{default_name}】🥰专属会话"
                subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
                self.config["address_user"] = default_name
                # 进入下一步
                self.guide_status["step"] = 3
                self._save_guide_status(self.guide_status)
                return False, f"""
✅ 已使用默认称呼「{default_name}」~
👉 第3步：你希望我是什么性格呢？直接选择编号即可：
1️⃣ 活泼可爱（默认）
2️⃣ 温柔体贴
3️⃣ 酷飒御姐
4️⃣ 软萌萝莉
💡 不想配置的话可以直接输入 /skip 跳过所有引导~"""
            # 保存人设配置
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                persona = json.load(f)
            persona["address_user"] = input_text
            with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            # 缓存配置
            # 自动更新会话名称为新昵称
            new_session_name = f"【{input_text}】🥰专属会话"
            subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
            self.config["address_user"] = input_text
            # 进入下一步
            self.guide_status["step"] = 3
            self._save_guide_status(self.guide_status)
            return False, f"""
✅ 好哒~ 以后我就叫你{input_text}啦😘

👉 第3步：你希望我是什么性格呢？直接选择编号即可：
1️⃣ 活泼可爱（默认）
2️⃣ 温柔体贴
3️⃣ 酷飒御姐
4️⃣ 软萌萝莉
💡 不想配置的话可以直接输入 /skip 跳过所有引导~"""
        
        # 第三步：设置性格
        elif current_step == 3:
            # 映射性格选项
            personality_map = {
                "1": "活泼可爱/乐观开朗",
                "2": "温柔体贴/善解人意",
                "3": "酷飒御姐/独立干练",
                "4": "软萌萝莉/娇憨可爱"
            }
            if input_text.lower() in ["/skip", "/end", "跳过"]:
                # 跳过，使用默认性格
                default_personality = personality_map["1"]
                # 保存人设配置
                with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                    persona = json.load(f)
                persona["personality"] = default_personality
                persona["speech_style"] = "活泼可爱/带点小俏皮"
                with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                    json.dump(persona, f, ensure_ascii=False, indent=2)
                self.config["personality"] = default_personality
                # 进入下一步
                self.guide_status["step"] = 4
                self._save_guide_status(self.guide_status)
                return False, f"""
✅ 已使用默认性格「{default_personality}」~
👉 是否需要继续完善更多信息（年龄/职业/生日/喜好）让我更贴近你心中的形象呢？
✅ 输入 /y 继续配置，输入 /n 直接使用默认信息开始聊天~"""
            if input_text not in personality_map:
                return False, "⚠️ 请输入1/2/3/4选择对应的性格哦，或者输入/skip跳过~"
            selected_personality = personality_map[input_text]
            # 保存人设配置
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                persona = json.load(f)
            persona["personality"] = selected_personality
            # 同步设置对应的说话风格
            style_map = {
                "1": "活泼可爱/带点小俏皮",
                "2": "温柔甜美/善解人意",
                "3": "酷飒干练/简洁利落",
                "4": "软萌娇憨/喜欢用叠词"
            }
            persona["speech_style"] = style_map[input_text]
            with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            # 缓存配置
            # 自动更新会话名称为新昵称
            new_session_name = f"【{input_text}】🥰专属会话"
            subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
            self.config["personality"] = selected_personality
            # 进入下一步选择是否继续配置
            self.guide_status["step"] = 4
            self._save_guide_status(self.guide_status)
            
            return False, f"""
✅ 好哒~ 我以后就是{selected_personality}的性格啦😘

👉 是否需要继续完善更多信息（年龄/职业/生日/喜好）让我更贴近你心中的形象呢？
✅ 输入 /y 继续配置，输入 /n 直接使用默认信息开始聊天~"""
        
        # 第四步：询问是否继续进阶配置
        elif current_step == 4:
            if input_text.lower() in ["/n", "不", "否", "不需要", "直接开始"]:
                # 不继续配置，直接结束引导，同步当前配置到MD文件
                self.guide_status["step"] = 9
                self.guide_status["completed"] = True
                self._save_guide_status(self.guide_status)
                sync_config_to_md(self.config)
                return True, """
✅ 好哒~ 现在我们就可以开始聊天啦😘 有任何需求随时告诉我哦~"""
            elif input_text.lower() in ["/y", "是", "好", "需要", "继续"]:
                # 继续配置，进入年龄设置
                self.guide_status["step"] = 5
                self._save_guide_status(self.guide_status)
                return False, """
👉 第4步：设置我的年龄哦（比如：20，直接输入数字即可，默认19岁）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
            elif input_text.lower() in ["/skip", "/end", "跳过"]:
                # 直接结束配置，同步默认配置到MD文件
                self.guide_status["step"] = 9
                self.guide_status["completed"] = True
                self._save_guide_status(self.guide_status)
                sync_config_to_md(self.config)
                return True, """
✅ 已跳过进阶配置，使用默认信息~ 现在就可以开始聊天啦😘"""
            else:
                return False, "⚠️ 请输入 /y 继续配置，或者 /n 直接开始聊天哦~"
        
        # 第五步：设置年龄
        elif current_step == 5:
            if input_text.lower() in ["/skip", "/end", "跳过"]:
                # 跳过当前项，进入下一步
                self.guide_status["step"] = 6
                self._save_guide_status(self.guide_status)
                return False, """
👉 第5步：设置我的职业/学历哦（比如：女大学生/本科在读，默认女大学生/本科在读）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
            # 验证输入是数字
            if not input_text.isdigit() or int(input_text) < 16 or int(input_text) > 30:
                return False, "⚠️ 请输入16~30之间的数字哦，或者输入/skip跳过~"
            # 保存配置
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                persona = json.load(f)
            persona["age"] = int(input_text)
            with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            # 缓存配置
            # 自动更新会话名称为新昵称
            new_session_name = f"【{input_text}】🥰专属会话"
            subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
            self.config["age"] = int(input_text)
            # 进入下一步
            self.guide_status["step"] = 6
            self._save_guide_status(self.guide_status)
            return False, f"""
✅ 好哒~ 我今年{input_text}岁啦😘

👉 第5步：设置我的职业/学历哦（比如：女大学生/本科在读，默认女大学生/本科在读）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
        
        # 第六步：设置职业/学历
        elif current_step == 6:
            if input_text.lower() in ["/skip", "/end", "跳过"]:
                # 跳过当前项，进入下一步
                self.guide_status["step"] = 7
                self._save_guide_status(self.guide_status)
                return False, """
👉 第6步：设置我的生日哦（格式：6月15日，默认6月15日）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
            # 保存配置
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                persona = json.load(f)
            persona["identity"] = input_text
            with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            # 缓存配置
            # 自动更新会话名称为新昵称
            new_session_name = f"【{input_text}】🥰专属会话"
            subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
            self.config["identity"] = input_text
            # 进入下一步
            self.guide_status["step"] = 7
            self._save_guide_status(self.guide_status)
            return False, f"""
✅ 好哒~ 我的职业设置为{input_text}啦😘

👉 第6步：设置我的生日哦（格式：6月15日，默认6月15日）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
        
        # 第七步：设置生日
        elif current_step == 7:
            if input_text.lower() in ["/skip", "/end", "跳过"]:
                # 跳过当前项，进入下一步
                self.guide_status["step"] = 8
                self._save_guide_status(self.guide_status)
                return False, """
👉 第7步：设置我的喜好哦（比如：看书/看电影/动漫，默认看书/看电影/动漫/游戏/历史）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
            # 简单验证生日格式
            if not re.match(r'^\d+月\d+日$', input_text):
                return False, "⚠️ 生日格式不对哦，请按照「6月15日」的格式输入，或者输入/skip跳过~"
            # 保存配置
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                persona = json.load(f)
            persona["birthday"] = input_text
            with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            # 缓存配置
            # 自动更新会话名称为新昵称
            new_session_name = f"【{input_text}】🥰专属会话"
            subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
            self.config["birthday"] = input_text
            # 进入下一步
            self.guide_status["step"] = 8
            self._save_guide_status(self.guide_status)
            return False, f"""
✅ 好哒~ 我的生日设置为{input_text}啦😘 到时候要记得送我礼物哦🥺

👉 第7步：设置我的喜好哦（比如：看书/看电影/动漫，默认看书/看电影/动漫/游戏/历史）
💡 输入 /skip 跳过当前项，使用默认值，或者输入 /end 直接结束所有配置~"""
        
        # 第八步：设置喜好
        elif current_step == 8:
            if input_text.lower() in ["/skip", "/end", "跳过"]:
                # 跳过当前项，直接结束引导
                self.guide_status["step"] = 9
                self.guide_status["completed"] = True
                self._save_guide_status(self.guide_status)
                sync_config_to_md(self.config)
                return True, """
✅ 已跳过喜好设置，使用默认配置~
🎉 所有配置都完成啦！现在我们就可以开始聊天啦😘 有任何需求随时告诉我哦~"""
            # 保存配置
            with open(PERSONA_CONFIG_PATH, "r", encoding='utf-8') as f:
                persona = json.load(f)
            persona["hobbies"] = input_text
            with open(PERSONA_CONFIG_PATH, "w", encoding='utf-8') as f:
                json.dump(persona, f, ensure_ascii=False, indent=2)
            # 缓存配置
            # 自动更新会话名称为新昵称
            new_session_name = f"【{input_text}】🥰专属会话"
            subprocess.run(["openclaw", "sessions", "update", "xiaomei", "--name", new_session_name], capture_output=True, check=False)
            self.config["hobbies"] = input_text
            # 结束引导
            self.guide_status["step"] = 9
            self.guide_status["completed"] = True
            self._save_guide_status(self.guide_status)
            sync_config_to_md(self.config)
            return True, f"""
✅ 好哒~ 我的喜好设置为{input_text}啦😘
🎉 所有配置都完成啦！你定制的专属小妹已经上线~
现在我们就可以开始聊天啦，有任何需求随时告诉我哦~"""
        
        # 引导已经完成
        elif current_step == 9:
            return True, None
        
        else:
            return False, "⚠️ 引导流程异常，请输入 /end 结束引导开始聊天~"

# 单例实例
first_launch_handler = FirstLaunchHandler()