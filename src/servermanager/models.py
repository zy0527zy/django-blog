from django.db import models

"""
src/servermanager/models.py
该模块定义Django ORM数据模型，映射数据库表。
包含命令存储模型、邮件发送日志模型。
"""

# Create your models here.
class commands(models.Model):
    """
    命令模型
    用于保存自定义执行命令，记录命令内容、描述和时间信息
    """
    title = models.CharField('命令标题', max_length=300)
    command = models.CharField('命令', max_length=2000)
    describe = models.CharField('命令描述', max_length=300)
    creation_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        """Django后台展示该模型对象时，返回命令标题"""
        return self.title

    class Meta:
        verbose_name = '命令'
        verbose_name_plural = verbose_name


class EmailSendLog(models.Model):
    """
    邮件发送日志模型
    记录每一次邮件发送的收件人、标题、内容以及发送是否成功
    """
    emailto = models.CharField('收件人', max_length=300)
    title = models.CharField('邮件标题', max_length=2000)
    content = models.TextField('邮件内容')
    send_result = models.BooleanField('结果', default=False)
    creation_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        """Django后台展示该日志对象时，返回邮件标题"""
        return self.title

    class Meta:
        verbose_name = '邮件发送log'
        verbose_name_plural = verbose_name
        ordering = ['-creation_time'] # 默认按创建时间倒序展示
