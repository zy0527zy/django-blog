#zly: 模块说明：定义 servermanager 的 Django ORM 数据模型。
"""
src/servermanager/models.py
该模块定义Django ORM数据模型，映射数据库表。
包含命令存储模型、邮件发送日志模型。
"""
from django.db import models


#zly: 模型定义入口（原注释：Create your models here.）。
class commands(models.Model):
    """
    命令模型
    用于保存自定义执行命令，记录命令内容、描述和时间信息
    """
    #zly: 命令标题：后台展示名，也是微信端输入的命令名。
    title = models.CharField('命令标题', max_length=300)
    #zly: 实际执行的 shell 命令文本，由 CommandHandler 执行。
    command = models.CharField('命令', max_length=2000)
    #zly: 命令描述：helpme 指令返回的帮助信息取自该字段。
    describe = models.CharField('命令描述', max_length=300)
    #zly: 创建时间：新增记录时由 Django 自动写入。
    creation_time = models.DateTimeField('创建时间', auto_now_add=True)
    #zly: 修改时间：每次保存时由 Django 自动刷新。
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    #zly: __str__：后台展示命令标题。
    def __str__(self):
        """Django后台展示该模型对象时，返回命令标题"""
        return self.title

    #zly: Meta：后台显示名“命令”。
    class Meta:
        verbose_name = '命令'
        verbose_name_plural = verbose_name


#zly: EmailSendLog：记录每次邮件发送的收件人、标题、正文与结果。
class EmailSendLog(models.Model):
    """
    邮件发送日志模型
    记录每一次邮件发送的收件人、标题、内容以及发送是否成功
    """
    #zly: 收件人邮箱地址。
    emailto = models.CharField('收件人', max_length=300)
    #zly: 邮件标题（长度 2000 沿用历史定义）。
    title = models.CharField('邮件标题', max_length=2000)
    #zly: 邮件正文（长文本）。
    content = models.TextField('邮件内容')
    #zly: 发送结果：True 成功、False 失败，默认失败。
    send_result = models.BooleanField('结果', default=False)
    #zly: 日志创建时间，自动写入。
    creation_time = models.DateTimeField('创建时间', auto_now_add=True)

    #zly: __str__：后台展示邮件标题。
    def __str__(self):
        """Django后台展示该日志对象时，返回邮件标题"""
        return self.title

    #zly: Meta：后台显示名“邮件发送log”，默认按创建时间倒序。
    class Meta:
        verbose_name = '邮件发送log'
        verbose_name_plural = verbose_name
        ordering = ['-creation_time']  #zly: 默认按创建时间倒序展示。
