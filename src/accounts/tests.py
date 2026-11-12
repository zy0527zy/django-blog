"""账号注册、登录、个人资料与密码管理功能测试。"""

from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import BlogUser
from blog.models import Article, Category
from djangoblog.utils import delete_sidebar_cache, generate_code, get_sha256

from . import utils


class AccountTest(TestCase):
    """测试账号注册、后台访问、邮箱验证和找回密码等流程。"""

    def setUp(self):
        """创建测试客户端、请求工厂及供账号流程复用的普通用户。"""
        self.client = Client()
        self.factory = RequestFactory()
        self.blog_user = BlogUser.objects.create_user(
            username="test",
            email="admin@admin.com",
            password="12345678"
        )
        self.new_test = "xxx123--="

    def test_validate_account(self):
        """验证超级用户登录后可访问管理后台及文章管理页面。"""
        user = BlogUser.objects.create_superuser(
            email="liangliangyy1@gmail.com",
            username="liangliangyy1",
            password="qwer!@#$ggg")
        loginresult = self.client.login(
            username='liangliangyy1',
            password='qwer!@#$ggg')
        self.assertEqual(loginresult, True)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

        category = Category()
        category.name = "categoryaaa"
        category.creation_time = timezone.now()
        category.last_modify_time = timezone.now()
        category.save()

        article = Article()
        article.title = "nicetitleaaa"
        article.body = "nicecontentaaa"
        article.author = user
        article.category = category
        article.type = 'a'
        article.status = 'p'
        article.save()

        response = self.client.get(article.get_admin_url())
        self.assertEqual(response.status_code, 200)

    def test_validate_register(self):
        """覆盖注册、邮箱验证、后台访问及退出后的访问状态。"""
        # 确认提交注册前数据库中还没有该邮箱对应的账号。
        self.assertEqual(
            0, len(
                BlogUser.objects.filter(
                    email='user123@user.com')))
        response = self.client.post(reverse('account:register'), {
            'username': 'user1233',
            'email': 'user123@user.com',
            'password1': 'password123!q@wE#R$T',
            'password2': 'password123!q@wE#R$T',
        })
        # 注册请求应创建账号，并生成用于邮箱验证的签名链接。
        self.assertEqual(
            1, len(
                BlogUser.objects.filter(
                    email='user123@user.com')))
        user = BlogUser.objects.filter(email='user123@user.com')[0]
        sign = get_sha256(get_sha256(settings.SECRET_KEY + str(user.id)))
        path = reverse('accounts:result')
        url = f'{path}?type=validation&id={user.id}&sign={sign}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.login(username='user1233', password='password123!q@wE#R$T')
        user = BlogUser.objects.filter(email='user123@user.com')[0]
        user.is_superuser = True
        user.is_staff = True
        user.save()
        # 权限变化后清理侧边栏缓存，再创建文章以检查后台详情页访问。
        delete_sidebar_cache()
        category = Category()
        category.name = "categoryaaa"
        category.creation_time = timezone.now()
        category.last_modify_time = timezone.now()
        category.save()

        article = Article()
        article.category = category
        article.title = "nicetitle333"
        article.body = "nicecontentttt"
        article.author = user

        article.type = 'a'
        article.status = 'p'
        article.save()

        response = self.client.get(article.get_admin_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('account:logout'))
        self.assertIn(response.status_code, [301, 302, 200])

        response = self.client.get(article.get_admin_url())
        self.assertIn(response.status_code, [301, 302, 200])

        response = self.client.post(reverse('account:login'), {
            'username': 'user1233',
            'password': 'password123'
        })
        self.assertIn(response.status_code, [301, 302, 200])

        response = self.client.get(article.get_admin_url())
        self.assertIn(response.status_code, [301, 302, 200])

    def test_verify_email_code(self):
        """验证有效验证码可通过，错误邮箱对应的验证码不能通过。"""
        to_email = "admin@admin.com"
        code = generate_code()
        utils.set_code(to_email, code)
        utils.send_verify_email(to_email, code)

        err = utils.verify("admin@admin.com", code)
        self.assertEqual(err, None)

        err = utils.verify("admin@123.com", code)
        self.assertEqual(type(err), str)

    def test_forget_password_email_code_success(self):
        """提交有效邮箱，检查找回密码验证码请求成功。"""
        resp = self.client.post(
            path=reverse("account:forget_password_code"),
            data={"email": "admin@admin.com"}
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("utf-8"), "ok")

    def test_forget_password_email_code_fail(self):
        """缺少邮箱或邮箱格式错误时，应返回邮箱错误提示。"""
        resp = self.client.post(
            path=reverse("account:forget_password_code"),
            data={}
        )
        self.assertEqual(resp.content.decode("utf-8"), "错误的邮箱")

        resp = self.client.post(
            path=reverse("account:forget_password_code"),
            data={"email": "admin@com"}
        )
        self.assertEqual(resp.content.decode("utf-8"), "错误的邮箱")

    def test_forget_password_email_success(self):
        """提交正确验证码和新密码后，确认账号密码已更新。"""
        code = generate_code()
        utils.set_code(self.blog_user.email, code)
        data = {
            "new_password1": self.new_test,
            "new_password2": self.new_test,
            "email": self.blog_user.email,
            "code": code,
        }
        resp = self.client.post(
            path=reverse("account:forget_password"),
            data=data
        )
        self.assertEqual(resp.status_code, 302)

        # 验证用户密码是否修改成功
        blog_user = BlogUser.objects.filter(
            email=self.blog_user.email,
        ).first()  # type: BlogUser
        self.assertNotEqual(blog_user, None)
        self.assertEqual(blog_user.check_password(data["new_password1"]), True)

    def test_forget_password_email_not_user(self):
        """尝试为不存在的邮箱重置密码时，请求应由视图正常处理。"""
        data = {
            "new_password1": self.new_test,
            "new_password2": self.new_test,
            "email": "123@123.com",
            "code": "123456",
        }
        resp = self.client.post(
            path=reverse("account:forget_password"),
            data=data
        )

        self.assertEqual(resp.status_code, 200)

    def test_forget_password_email_code_error(self):
        """验证码不匹配时，不应完成密码重置。"""
        code = generate_code()
        utils.set_code(self.blog_user.email, code)
        data = {
            "new_password1": self.new_test,
            "new_password2": self.new_test,
            "email": self.blog_user.email,
            "code": "111111",
        }
        resp = self.client.post(
            path=reverse("account:forget_password"),
            data=data
        )

        self.assertEqual(resp.status_code, 200)

    #swb: 验证资料编辑页只允许登录用户访问并更新当前用户资料。
    def test_profile_update_and_login_required(self):
        """未登录用户被拒绝访问；登录用户可保存个人资料和有效头像。"""
        response = self.client.get(reverse('account:profile'))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.blog_user)
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(image_buffer, format='PNG')
        avatar = SimpleUploadedFile(
            'avatar.png', image_buffer.getvalue(), content_type='image/png')
        response = self.client.post(reverse('account:profile'), {
            'nickname': '文博',
            'bio': '热爱写作',
            'avatar': avatar,
        })
        self.assertEqual(response.status_code, 302)
        self.blog_user.refresh_from_db()
        self.assertEqual(self.blog_user.nickname, '文博')
        self.assertEqual(self.blog_user.bio, '热爱写作')
        self.assertTrue(self.blog_user.avatar.name.startswith('accounts/avatars/'))
        self.blog_user.avatar.delete(save=False)

    #swb: 验证改密需要正确旧密码，保存后新密码生效且会话保持登录。
    def test_change_password_checks_old_password_and_keeps_session(self):
        """错误旧密码不能修改密码；修改成功后新密码生效且当前会话保持登录。"""
        self.client.force_login(self.blog_user)
        response = self.client.post(reverse('account:change_password'), {
            'old_password': 'wrong-password',
            'new_password1': 'New-safe-pass-983!',
            'new_password2': 'New-safe-pass-983!',
        })
        self.assertEqual(response.status_code, 200)
        self.blog_user.refresh_from_db()
        self.assertTrue(self.blog_user.check_password('12345678'))

        response = self.client.post(reverse('account:change_password'), {
            'old_password': '12345678',
            'new_password1': 'New-safe-pass-983!',
            'new_password2': 'New-safe-pass-983!',
        })
        self.assertEqual(response.status_code, 302)
        self.blog_user.refresh_from_db()
        self.assertTrue(self.blog_user.check_password('New-safe-pass-983!'))
        self.assertTrue(self.client.get(reverse('account:profile')).wsgi_request.user.is_authenticated)
