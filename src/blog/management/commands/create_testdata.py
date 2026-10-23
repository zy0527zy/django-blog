#hzh: 本模块生成测试账号、分类、标签等示例数据，仅用于测试环境。
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from blog.models import Article, Tag, Category


class Command(BaseCommand):
    help = 'create test datas'

    #hzh: 命令会实际写入数据库，并使用固定测试账号信息，不应直接用于生产环境。
    def handle(self, *args, **options):
        user = get_user_model().objects.get_or_create(
            email='test@test.com', username='测试用户', password=make_password('test!q@w#eTYU'))[0]

        pcategory = Category.objects.get_or_create(
            name='我是父类目', parent_category=None)[0]

        category = Category.objects.get_or_create(
            name='子类目', parent_category=pcategory)[0]

        category.save()
        basetag = Tag()
        basetag.name = "标签"
        basetag.save()
        for i in range(1, 20):
            article = Article.objects.get_or_create(
                category=category,
                title='nice title ' + str(i),
                body='nice content ' + str(i),
                author=user)[0]
            tag = Tag()
            tag.name = "标签" + str(i)
            tag.save()
            article.tags.add(tag)
            article.tags.add(basetag)
            article.save()

        from djangoblog.utils import cache
        cache.clear()
        self.stdout.write(self.style.SUCCESS('created test datas \n'))
