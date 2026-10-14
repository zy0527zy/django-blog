import logging

from django import forms
from haystack.forms import SearchForm

logger = logging.getLogger(__name__)


# 博客全文搜索表单，在 Haystack 搜索表单基础上增加查询字段
class BlogSearchForm(SearchForm):
    querydata = forms.CharField(required=True)

    # 校验搜索内容并调用 Haystack 执行全文搜索
    def search(self):
        datas = super(BlogSearchForm, self).search()
        if not self.is_valid():
            return self.no_query_found()

        if self.cleaned_data['querydata']:
            logger.info(self.cleaned_data['querydata'])
        return datas
