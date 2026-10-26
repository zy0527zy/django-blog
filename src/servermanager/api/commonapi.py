#zly: 模块说明：公共能力接口封装，包含 OpenAI 对话接口与系统命令执行处理器。
"""
servermanager/api/commonapi.py 文件
功能：公共能力接口封装，包含ChatGPT对话接口、系统命令执行处理器
供微信机器人调用，实现AI对话和管理员远程执行预定义系统命令
"""
import logging
import os
from functools import lru_cache

import openai
from openai import OpenAI

from servermanager.models import commands

#zly: 模块日志实例。
logger = logging.getLogger(__name__)


#zly: 按需创建 OpenAI 客户端单例；httpx 默认读取 HTTP_PROXY/HTTPS_PROXY 环境变量。
@lru_cache(maxsize=1)
def _get_openai_client():
    """创建并复用 OpenAI 客户端，避免未配置密钥时在模块导入阶段抛错。"""
    return OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))


#zly: ChatGPT：调用 OpenAI 接口完成文本对话的静态工具类。
class ChatGPT:
    """ChatGPT对话静态工具类，调用OpenAI接口完成文本对话"""

    #zly: 发送一条用户消息并返回模型回复；异常统一捕获并返回友好提示。
    @staticmethod
    def chat(prompt):
        """
        静态对话方法，向GPT3.5-turbo发送用户提示词并返回回答
        :param prompt: 用户输入的对话文本
        :return: AI返回内容，异常时返回错误提示
        """
        try:
            #zly: 调用 openai 聊天接口（openai>=1.0 的 client.chat.completions 写法）。
            completion = _get_openai_client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content
        except (openai.OpenAIError, IndexError, AttributeError) as exc:
            #zly: 捕获接口调用异常，记录错误日志并返回友好提示。
            logger.error('OpenAI 调用失败: %s', exc)
            return "服务器出错了"


#zly: CommandHandler：加载数据库中的预定义命令，提供查找、执行与帮助信息。
class CommandHandler:
    """系统命令处理类，加载数据库预定义命令，提供命令查找、执行、帮助信息查询"""

    #zly: 初始化时取出全部命令（QuerySet 惰性求值）。
    def __init__(self):
        """构造方法：读取数据库中全部预定义命令并缓存"""
        self.commands = commands.objects.all()

    #zly: 根据命令标题查找并执行对应的系统命令。
    def run(self, title):
        """
        根据命令标题查找并执行对应的系统命令
        :param title: 命令标题名称
        :return: 命令输出结果，找不到命令返回提示文本
        """
        #zly: 过滤匹配标题（忽略大小写）。
        cmd = [
            item for item in self.commands
            if item.title.upper() == title.upper()
        ]
        if cmd:
            return self.__run_command__(cmd[0].command)
        return "未找到相关命令，请输入hepme获得帮助。"

    #zly: 私有方法：执行系统 shell 命令并读取输出。
    def __run_command__(self, cmd):
        """
        私有方法：执行系统shell命令并读取输出
        :param cmd: 待执行的shell命令字符串
        :return: 命令控制台输出，捕获异常返回执行错误提示
        """
        try:
            #zly: os.popen 执行 shell 命令，读取命令输出内容。
            return os.popen(cmd).read()
        except OSError:
            return '命令执行出错!'

    #zly: 拼接所有预定义命令的标题与描述，返回帮助文本。
    def get_help(self):
        """拼接所有预定义命令的标题与描述，返回帮助文本信息"""
        rsp = ''
        for cmd in self.commands:
            rsp += f'{cmd.title}:{cmd.describe}\n'
        return rsp


#zly: 模块单独运行时的测试入口，测试 ChatGPT 对话功能。
if __name__ == '__main__':
    chatbot = ChatGPT()
    test_prompt = "写一篇1000字关于AI的论文"
    print(chatbot.chat(test_prompt))
