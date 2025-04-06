from astrbot.api.event.filter import event_message_type, EventMessageType, command
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import *
from collections import defaultdict
from typing import List
import re

@register("astrbot_plugin_repeat_after_me", "和泉智宏", "跟读插件", "1.0.0", "")
class FollowReadingPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.disabled_groups = set()
        self.config = config or {}
        self.commands = {
            "跟我说": self.do_follow_reading
        }
        
    @command("repeat")
    async def handle_repeat(self, event: AstrMessageEvent, operation: str = ""):
        '''repeat 命令处理
        
        Args:
            operation(string): on/off 开启或关闭跟读功能
        '''
        if not event.message_obj.group_id:
            yield event.plain_result("此命令仅在群聊中可用")
            return
            
        if operation == "off":
            self.disabled_groups.add(event.message_obj.group_id)
            yield event.plain_result("已在本群关闭跟读功能")
        elif operation == "on":
            self.disabled_groups.discard(event.message_obj.group_id)
            yield event.plain_result("已在本群开启跟读功能")
        else:
            yield event.plain_result("用法: /repeat [on|off]")

    def extract_follow_content(self, message_str: str) -> str:
        """从消息文本中提取'跟我说xxx'中的xxx内容"""
        match = re.search(r'跟\s*我\s*说\s*([\s\S]*)', message_str)
        if match:
            content = match.group(1).strip()
            return content
        return None

    def is_at_me(self, message, self_id):
        """检测消息是否@了机器人"""
        for msg in message:
            if isinstance(msg, At):
                for attr in ['qq', 'target', 'user_id', 'target_id', 'id']:
                    if hasattr(msg, attr):
                        target_id = getattr(msg, attr)
                        if str(target_id) == str(self_id):
                            return True
        return False
    
    async def do_follow_reading(self, event: AstrMessageEvent):
        """处理跟读命令"""
        # 获取消息内容
        message_str = event.message_str.strip()
        
        # 提取要跟读的内容
        content = self.extract_follow_content(message_str)
        if not content:
            return
            
        yield event.plain_result(content)

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        '''自动跟读"跟我说xxx"的消息'''
        try:
            # 基本检查
            if not hasattr(event, 'message_obj') or not event.message_obj.message:
                return
                
            # 获取机器人ID
            self_id = event.message_obj.self_id
            
            # 检查群是否已禁用
            if event.message_obj.group_id and event.message_obj.group_id in self.disabled_groups:
                return
                
            # 检查是否@了机器人
            if not self.is_at_me(event.message_obj.message, self_id):
                return
            
            message_str = event.message_str.strip()
            
            for command, func in self.commands.items():
                if command in message_str:
                    async for result in func(event):
                        yield result
                    break
                    
        except Exception as e:
            pass
