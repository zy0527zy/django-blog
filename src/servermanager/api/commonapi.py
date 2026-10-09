"""
servermanager/api/commonapi.py 文件
功能：公共能力接口封装，包含ChatGPT对话接口、系统命令执行处理器
供微信机器人调用，实现AI对话和管理员远程执行预定义系统命令
"""
import logging
import os
import openai
from servermanager.models import commands

# 日志实例
logger = logging.getLogger(__name__)
# 读取环境变量中的OpenAI密钥
openai.api_key = os.environ.get('OPENAI_API_KEY')
# 如果配置了HTTP代理，则设置openai代理
if os.environ.get('HTTP_PROXY'):
    openai.proxy = os.environ.get('HTTP_PROXY')


"""ChatGPT对话静态工具类，调用OpenAI接口完成文本对话"""
class ChatGPT:
    """
    静态对话方法，向GPT3.5-turbo发送用户提示词并返回回答
    :param prompt: 用户输入的对话文本
    :return: AI返回内容，异常时返回错误提示
    """
    @staticmethod
    def chat(prompt):
        try:
            # 调用openai聊天接口，传入用户消息
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                      messages=[{"role": "user", "content": prompt}])
            return completion.choices[0].message.content
        except Exception as e:
            # 捕获接口调用异常，记录错误日志，返回友好提示
            logger.error(e)
            return "服务器出错了"


"""系统命令处理类，加载数据库预定义命令，提供命令查找、执行、帮助信息查询"""
class CommandHandler:
    """构造方法：读取数据库中全部预定义命令并缓存"""
    def __init__(self):
        self.commands = commands.objects.all()

    """
    根据命令标题查找并执行对应的系统命令
    :param title: 命令标题名称
    :return: 命令输出结果，找不到命令返回提示文本
    """
    def run(self, title):
        """
        运行命令
        :param title: 命令
        :return: 返回命令执行结果
        """
        # 过滤匹配标题（忽略大小写）
        cmd = list(
            filter(
                lambda x: x.title.upper() == title.upper(),
                self.commands))
        if cmd:
            return self.__run_command__(cmd[0].command)
        else:
            return "未找到相关命令，请输入hepme获得帮助。"

    """
    私有方法：执行系统shell命令并读取输出
    :param cmd: 待执行的shell命令字符串
    :return: 命令控制台输出，捕获异常返回执行错误提示
    """
    def __run_command__(self, cmd):
        try:
            # os.popen执行shell命令，读取命令输出内容
            res = os.popen(cmd).read()
            return res
        except BaseException:
            return '命令执行出错!'

    """拼接所有预定义命令的标题与描述，返回帮助文本信息"""
    def get_help(self):
        rsp = ''
        for cmd in self.commands:
            rsp += '{c}:{d}\n'.format(c=cmd.title, d=cmd.describe)
        return rsp


# 模块单独运行时的测试入口，测试ChatGPT对话功能
if __name__ == '__main__':
    chatbot = ChatGPT()
    prompt = "写一篇1000字关于AI的论文"
    print(chatbot.chat(prompt))
