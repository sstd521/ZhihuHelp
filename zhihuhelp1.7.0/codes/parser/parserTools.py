# -*- coding: utf-8 -*-

import re
import datetime  # 简单处理时间

from codes.baseClass import *
from bs4 import BeautifulSoup
import copy #用于复制对象（仅用了一次）

class ParserTools(BaseClass):
    @staticmethod
    def get_yesterday():
        today = datetime.date.today()
        one = datetime.timedelta(days=1)
        yesterday = today - one
        return yesterday.isoformat()

    @staticmethod
    def get_today():
        return datetime.date.today().isoformat()

    @staticmethod
    def match_content(patten, content, default=""):
        result = re.search(patten, str(content))
        if result is None:
            return default
        return result.group(0)

    @staticmethod
    def match_int(content):
        u"""
        返回文本形式的文字中最长的数字串，若没有则返回'0'
        """
        return ParserTools.match_content("\d+", content, "0")

    @staticmethod
    def match_question_id(rawLink):
        return ParserTools.match_content("(?<=question/)\d{8}", rawLink)

    @staticmethod
    def match_answer_id(rawLink):
        return ParserTools.match_content("(?<=answer/)\d{8}", rawLink)

    @staticmethod
    def match_topic_id(rawLink):
        return ParserTools.match_content("(?<=topic/)\d+", rawLink)

    @staticmethod
    def match_collection_id(rawLink):
        return ParserTools.match_content("(?<=collection/)\d+", rawLink)

    @staticmethod
    def match_author_id(rawLink):
        return ParserTools.match_content("""(?<=people/)[^/'"]+""", rawLink)

    @staticmethod
    def get_tag_content(tag):
        u"""
        用于提取bs中tag.contents的内容
        """
        return "".join([unicode(x) for x in tag.contents])

    @staticmethod
    def get_attr(dom, attr, defaultValue=""):
        u"""
        获取bs中tag.content的指定属性
        若content为空或者没有指定属性则返回默认值
        """
        if dom is None:
            return defaultValue
        return dom.get(attr, defaultValue)

    @staticmethod
    def parse_date(date='1357-08-12'):
        if u'昨天' in date:
            return ParserTools.get_yesterday()
        if u'今天' in date:
            return ParserTools.get_today()
        return ParserTools.match_content(r'\d{4}-\d{2}-\d{2}', date, date)  # 一三五七八十腊，三十一天永不差！


class Author(ParserTools):
    """
    实践一把《代码整洁之道》的做法，以后函数尽量控制在5行之内
    """

    def __init__(self, dom=None):
        self.set_dom(dom)
        return

    def set_dom(self, dom):
        self.info = {}
        if dom:
            self.dom = dom.find('div', class_='zm-item-answer-author-info')
        return

    def get_info(self):
        self.parse_info()
        return self.info

    def parse_info(self):
        if self.dom.find('img') is None:
            self.create_anonymous_info()
        else:
            self.parse_author_info()
        return self.info

    def parse_author_info(self):
        self.parse_author_id()
        self.parse_author_sign()
        self.parse_author_logo()
        self.parse_author_name()
        return

    def create_anonymous_info(self):
        self.info['author_id'] = u"coder'sGirlFriend~"
        self.info['author_sign'] = u''
        self.info['author_logo'] = u'http://pic1.zhimg.com/da8e974dc_s.jpg'
        self.info['author_name'] = u'匿名用户'
        return

    def parse_author_id(self):
        author = self.dom.find('a', class_='zm-item-link-avatar')
        if not author:
            BaseClass.logger.debug(u'用户ID未找到')
            return
        link = self.get_attr(author, 'href')
        self.info['author_id'] = self.match_author_id(link)
        return

    def parse_author_sign(self):
        sign = self.dom.find('strong', class_='zu-question-my-bio')
        if not sign:
            BaseClass.logger.debug(u'用户签名未找到')
            return
        self.info['author_sign'] = self.get_attr(sign, 'title')
        return

    def parse_author_logo(self):
        self.info['author_logo'] = self.get_attr(self.dom.find('img'), 'src')
        return

    def parse_author_name(self):
        name = self.dom.find('a', class_='author-link')
        if not name:
            BaseClass.logger.debug(u'用户名未找到')
            return
        self.info['author_name'] = name.text
        return


class Answer(ParserTools):
    def __init__(self, dom=None):
        self.set_dom(dom)
        self.author_parser = Author()
        return

    def set_dom(self, dom):
        self.info = {}
        if dom and not(dom.select('div.answer-status')) :
            self.header = dom.find('div', class_='zm-item-vote-info')
            self.body   = dom.find('div', class_='zm-editable-content')
            self.footer = dom.find('div', class_='zm-meta-panel')
            self.author_parser.set_dom(dom)
        return

    def get_info(self):
        answer_info = self.parse_info()
        author_info = self.author_parser.get_info()
        return dict(answer_info, **author_info)

    def parse_info(self):
        self.parse_header_info()
        self.parse_answer_content()
        self.parse_footer_info()
        return self.info

    def parse_header_info(self):
        self.parse_vote_count()
        return

    def parse_footer_info(self):
        self.parse_date_info()
        self.parse_comment_count()
        self.parse_no_record_flag()
        self.parse_href_info()
        return

    def parse_vote_count(self):
        if not self.header:
            BaseClass.logger.debug(u'答案赞同数未找到')
            return
        self.info['agree'] = self.get_attr(self.header, 'data-votecount')
        return

    def parse_answer_content(self):
        if not self.body:
            BaseClass.logger.debug(u'答案内容未找到')
            return
        self.info['content'] = self.get_tag_content(self.body)
        return

    def parse_date_info(self):
        data_block = self.footer.find('a', class_='answer-date-link')
        commit_date = self.get_attr(data_block, 'data-tip')
        if not data_block:
            BaseClass.logger.debug(u'答案更新日期未找到')
            return

        if commit_date:
            update_date = data_block.get_text()
            self.info['edit_date'] = self.parse_date(update_date)
            self.info['commit_date'] = self.parse_date(commit_date)
        else:
            commit_date = data_block.get_text()
            self.info['edit_date'] = self.info['commit_date'] = self.parse_date(commit_date)

    def parse_comment_count(self):
        # BS的属性选择器语法区分“和’！！！
        # 还好知乎所有的属性都是双引号- -
        # 看看人家这软件工程做的！
        comment = self.footer.select('a[name="addcomment"]')
        if not comment:
            BaseClass.logger.debug(u'评论数未找到')
            return
        self.info['comment'] = self.match_int(comment[0].get_text())
        return

    def parse_no_record_flag(self):
        no_record_flag = self.footer.find('a', class_='copyright')
        if not no_record_flag:
            BaseClass.logger.debug(u'禁止转载标志未找到')
            return
        self.info['no_record_flag'] = int(u'禁止转载' in no_record_flag.get_text())
        return

    def parse_href_info(self):
        href_tag = self.footer.find('a', class_='answer-date-link')
        if not href_tag:
            BaseClass.logger.debug(u'问题id，答案id未找到')
            return
        href = self.get_attr(href_tag, 'href')
        self.parse_question_id(href)
        self.parse_answer_id(href)
        self.info['href'] = "http://www.zhihu.com/question/{question_id}/answer/{answer_id}".format(**self.info)
        return

    def parse_question_id(self, href):
        self.info['question_id'] = self.match_question_id(href)
        return

    def parse_answer_id(self, href):
        self.info['answer_id'] = self.match_answer_id(href)
        return

class SimpleAnswer(Answer):
    def set_dom(self, dom):
        self.info = {}
        if dom and not(dom.select('div.answer-status')):
            self.header = dom.find('div', class_='zm-item-vote-info')
            self.body   = dom.find('textarea', class_='content')
            self.footer = dom.find('div', class_='zm-meta-panel')
            if self.body:
                self.content = BeautifulSoup(self.get_tag_content(self.body), 'html.parser')
            self.author_parser.set_dom(dom)
        return

    def parse_answer_content(self):
        #移除无用的span元素
        if not self.content:
            BaseClass.logger.debug(u'答案内容未找到')
            return
        content = copy.deepcopy(self.content)
        span = content.find('span', class_='answer-date-link-wrap')
        if not span:
            BaseClass.logger.debug(u'答案内容未找到')
            return
        span.extract()
        self.info['content'] = self.get_tag_content(content)
        return

    def parse_date_info(self):
        if not self.content:
            BaseClass.logger.debug(u'答案更新日期未找到')
            return
        data_block = self.content.find('a', class_='answer-date-link')
        if not data_block:
            BaseClass.logger.debug(u'答案更新日期未找到')
            return
        commit_date = self.get_attr(data_block, 'data-tip')
        if commit_date:
            update_date = data_block.get_text()
            self.info['edit_date'] = self.parse_date(update_date)
            self.info['commit_date'] = self.parse_date(commit_date)
        else:
            commit_date = data_block.get_text()
            self.info['edit_date'] = self.info['commit_date'] = self.parse_date(commit_date)

    def parse_href_info(self):
        if not self.content:
            BaseClass.logger.debug(u'答案更新日期未找到')
            return
        href_tag = self.content.find('a', class_='answer-date-link')
        if not href_tag:
            BaseClass.logger.debug(u'问题id，答案id未找到')
            return
        href = self.get_attr(href_tag, 'href')
        self.parse_question_id(href)
        self.parse_answer_id(href)
        self.info['href'] = "http://www.zhihu.com/question/{question_id}/answer/{answer_id}".format(**self.info)
        return


class SimpleQuestion(ParserTools):
    def __init__(self, dom=None):
        self.set_dom(dom)
        return

    def set_dom(self, dom):
        self.info = {}
        if dom:
            self.dom = dom
        return

    def get_info(self):
        self.parse_info()
        return self.info

    def parse_info(self):
        self.parse_question_id()
        self.parse_title()
        return self.info

    def parse_question_id(self):
        question = self.dom.select('h2 a.question_link')
        if not question:
            question = self.dom.select('h2.zm-item-title a[target="_blank"]')# 在收藏夹中需要使用这种选择器
        if not question:
            BaseClass.logger.debug(u'问题信息_id未找到')
            return
        href = self.get_attr(question[0], 'href')
        self.info['question_id'] = self.match_question_id(href)
        return

    def parse_title(self):
        question = self.dom.select('h2 a.question_link')
        if not question:
            question = self.dom.select('h2.zm-item-title a[target="_blank"]')# 在收藏夹中需要使用这种选择器
        if not question:
            BaseClass.logger.debug(u'问题信息_title未找到')
            return
        self.info['title'] = question[0].get_text()
        return


class QuestionInfo(ParserTools):
    """
        特指single_question 和 single_answer中的内容
    """

    def __init__(self, dom=None):
        self.set_dom(dom)
        return

    def set_dom(self, dom):
        self.info = {}
        if dom:
            self.dom = dom
            self.side_dom = dom.find('div', class_='zu-main-sidebar')
        return

    def get_info(self):
        self.parse_info()
        return self.info

    def parse_info(self):
        self.parse_base_info()
        self.parse_status_info()
        return self.info

    def parse_base_info(self):
        self.parse_question_id()
        self.parse_title()
        self.parse_description()
        self.parse_comment_count()
        return

    def parse_question_id(self):
        meta = self.dom.select('meta[http-equiv="mobile-agent"]')
        if not meta:
            BaseClass.logger.debug(u'问题ID未找到')
            return
        content = self.get_attr(meta[0], 'content', 0)
        self.info['question_id'] = self.match_question_id(content)
        return

    def parse_title(self):
        title = self.dom.select('#zh-question-title h2')
        if not title:
            BaseClass.logger.debug(u'问题标题未找到')
            return
        self.info['title'] = title[0].get_text()
        return

    def parse_description(self):
        description = self.dom.select('#zh-question-detail div.zm-editable-content')
        if not description:
            BaseClass.logger.debug(u'问题描述未找到')
            return
        self.info['description'] = self.get_tag_content(description[0])
        return

    def parse_comment_count(self):
        comment = self.dom.select('#zh-question-meta-wrap a[name="addcomment"]')
        if not comment:
            BaseClass.logger.debug(u'问题评论数未找到')
            return
        self.info['comment'] = self.match_int(comment[0].get_text())
        return

    def parse_status_info(self):
        self.parse_views()
        self.parse_followers_count()
        return

    def parse_followers_count(self):
        followers_count = self.side_dom.select('div.zh-question-followers-sidebar div.zg-gray-normal strong')
        if followers_count:
            self.info['followers'] = self.match_int(followers_count[0].get_text())
        return

    def parse_views(self):
        div = self.side_dom.find_all('div', class_='zm-side-section')[-1]
        views = div.find('strong')  # 在最后一个side-section中的第一个strong是问题浏览次数
        self.info['views'] = self.match_int(views.get_text())
        return

    def parse_answer_count(self):
        self.info['answers'] = 0  # 默认为0
        count = self.dom.select('#zh-answers-title a.zg-link-litblue, #zh-question-answer-num')
        if count:
            self.info['answers'] = self.match_int(count[0].get_text())
        return


class AuthorInfo(ParserTools):
    u"""
    使用详情页面进行解析
    """

    def __init__(self, dom=None):
        self.set_dom(dom)
        return

    def set_dom(self, dom):
        self.info = {}
        if dom:
            self.dom = dom
            self.header_dom = dom.find('div', class_='zm-profile-header')
            self.detail_dom = dom.find('div', class_='zm-profile-details-wrap')
            self.side_dom = dom.find('div', class_='zu-main-sidebar')
        return

    def get_info(self):
        self.parse_info()
        return self.info

    def parse_info(self):
        self.parse_base_info()
        self.parse_detail_info()
        self.parse_extra_info()
        return self.info

    def parse_base_info(self):
        self.parse_author_id()
        self.parse_author_hash()
        self.parse_name()
        self.parse_sign()
        self.parse_logo()
        self.parse_description()
        self.parse_weibo()
        self.parse_gender()
        return

    def parse_name(self):
        name = self.dom.select('div.title-section a.name')
        if not name:
            BaseClass.logger.debug(u'用户名未找到')
            return
        self.info['name'] = name[0].get_text()
        return

    def parse_weibo(self):
        weibo = self.header_dom.select('a.zm-profile-header-user-weibo')
        if not weibo:
            BaseClass.logger.debug(u'用户微博未找到')
            return
        self.info['weibo'] = self.get_attr(weibo[0], 'href')
        return

    def parse_sign(self):
        sign = self.dom.select('div.title-section span[title]')
        if not sign:
            BaseClass.logger.debug(u'用户签名未找到')
            return
        self.info['sign'] = self.get_attr(sign[0], 'title')
        return

    def parse_logo(self):
        logo = self.header_dom.select('div.zm-profile-header-avatar-container img.avatar')
        if not logo:
            BaseClass.logger.debug(u'用户头像未找到')
            return
        self.info['logo'] = self.get_attr(logo[0], 'src')
        return

    def parse_gender(self):
        gender = self.header_dom.select('span.edit-wrap input[checked="checked"]')
        if not gender:
            BaseClass.logger.debug(u'用户性别未找到')
            return
        self.info['gender'] = self.get_attr(gender[0], 'class')[0] #class为多值属性，返回数据为一个列表，所以需要进行特殊处理
        return

    def parse_author_id(self):
        item = self.header_dom.select('div.profile-navbar a.item')
        if not item:
            BaseClass.logger.debug(u'用户id未找到')
            return
        href = self.get_attr(item[0], 'href')
        self.info['author_id'] = self.match_author_id(href)
        return

    def parse_author_hash(self):
        hash = self.dom.select('script[data-name="current_people"]')
        if not hash:
            BaseClass.logger.debug(u'用户hash未找到')
            return
        hash = hash[0].get_text().split(',')[-1]  # 取出hash所在字符串
        self.info['hash'] = hash.split('"')[1]  # 取出hash值
        return

    def parse_profile_count(self):
        def parse_items(root=None, kind='asks'):
            node = root.select('a[href*="{} span.num"]'.format(kind))
            if not node:
                BaseClass.logger.debug(u'{}未找到'.format(kind))
            self.info[kind] = self.match_int(node[0].get_text())
            return

        item_list = ['asks', 'answers', 'posts', 'collections', 'logs']
        div = self.header_dom.select('div.profile-navbar')
        if not div:
            BaseClass.logger.debug(u'用户提问-回答-专栏数未找到')
            return
        for item in item_list:
            parse_items(div[0], item)
        return

    def parse_detail_info(self):
        detail_items = ['agree', 'thanks', 'collected', 'shared']
        detail = self.detail_dom.select('.zm-profile-module-desc span strong')
        if not detail:
            BaseClass.logger.debug(u'用户赞同-感谢-被收藏数未找到')
            return
        for i in range(len(detail)):
            self.info[detail_items[i]] = self.match_int(detail[i])
        return

    def parse_description(self):
        description = self.header_dom.select('.description span.content')
        if not description:
            BaseClass.logger.debug(u'用户详情未找到')
            return
        self.info['description'] = self.get_tag_content(description[0])
        return

    def parse_extra_info(self):
        self.parse_followee()
        self.parse_follower()
        self.parse_followed_column()
        self.parse_followed_topic()
        self.parser_views()
        return

    def parse_followee(self):
        followee = self.side_dom.select('div.zm-profile-side-following a[href*="followees"] strong')
        if not followee:
            BaseClass.logger.debug(u'用户关注数未找到')
            return
        self.info['followee'] = followee[0].get_text()
        return

    def parse_follower(self):
        follower = self.side_dom.select('div.zm-profile-side-following a[href*="followers"] strong')
        if not follower:
            BaseClass.logger.debug(u'用户粉丝数未找到')
            return
        self.info['follower'] = follower[0].get_text()
        return

    def parse_followed_column(self):
        column = self.side_dom.select('.zm-profile-side-section-title a[href*="columns"] strong')
        if not column:
            BaseClass.logger.debug(u'用户关注专栏数未找到')
            return
        self.info['followed_column'] = self.match_int(column[0].get_text())
        return

    def parse_followed_topic(self):
        topic = self.side_dom.select('.zm-profile-side-section-title a[href*="topics"] strong')
        if not topic:
            BaseClass.logger.debug(u'用户关注话题数未找到')
            return
        self.info['followed_topic'] = self.match_int(topic[0].get_text())
        return

    def parser_views(self):
        views = self.side_dom.select('.zm-profile-side-section .zm-side-section-inner span.zg-gray-normal strong')
        if not views:
            BaseClass.logger.debug(u'用户被浏览数未找到')
            return
        self.info['viewed'] = views[0].get_text()
        return


class TopicInfo(ParserTools):
    def __init__(self, dom=None):
        self.set_dom(dom)
        return

    def set_dom(self, dom):
        self.info = {}
        if dom:
            self.dom = dom
        return

    def get_info(self):
        self.parse_info()
        return self.info

    def parse_info(self):
        self.parse_title()
        self.parse_topic_id()
        self.parse_logo()
        self.parse_follower()
        self.parse_description()
        return self.info

    def parse_title(self):
        title = self.dom.select('#zh-topic-title h1.zm-editable-content')
        if not title:
            BaseClass.logger.debug(u'话题标题未找到')
        self.info['title'] = title[0].get_text()
        return

    def parse_topic_id(self):
        topic = self.dom.select('link[rel="canonical"]')
        if not topic:
            BaseClass.logger.debug(u'话题id未找到')
        href = self.get_attr(topic[0], 'href')
        self.info['topic_id'] = self.match_topic_id(href)
        return

    def parse_logo(self):
        logo = self.dom.select('img.zm-avatar-editor-preview')
        if not logo:
            BaseClass.logger.debug(u'话题图标未找到')
        self.info['logo'] = self.get_attr(logo[0], 'src')
        return

    def parse_follower(self):
        follower = self.dom.select('div.zm-topic-side-followers-info a strong')
        if not follower:
            BaseClass.logger.debug(u'话题关注人数未找到')
        self.info['follower'] = follower[0].get_text()
        return

    def parse_description(self):
        description = self.dom.select('#zh-topic-desc div.zm-editable-content')
        if not description:
            BaseClass.logger.debug(u'话题描述未找到')
        self.info['description'] = self.get_tag_content(description[0])
        return


class CollectionInfo(ParserTools):
    u"""
    只解析收藏夹相关信息，暂时不解析创建者相关的信息
    """

    def __init__(self, dom=None):
        self.set_dom(dom)
        return

    def set_dom(self, dom):
        self.info = {}
        if dom:
            self.dom = dom
        return

    def get_info(self):
        self.parse_info()
        return self.info

    def parse_info(self):
        self.parse_title()
        self.parse_collection_id()
        self.parse_follower()
        self.parse_description()
        self.parse_comment_count()
        return self.info

    def parse_title(self):
        title = self.dom.select('h2#zh-fav-head-title')
        if not title:
            BaseClass.logger.debug(u'收藏夹标题未找到')
        self.info['title'] = title[0].get_text()
        return

    def parse_collection_id(self):
        topic = self.dom.select('meta[http-equiv="mobile-agent"]')
        if not topic:
            BaseClass.logger.debug(u'话题id未找到')
        href = self.get_attr(topic[0], 'content')
        self.info['collection_id'] = self.match_collection_id(href)
        return

    def parse_follower(self):
        follower = self.dom.select(
            'div.zm-side-section div.zm-side-section-inner div.zg-gray-normal a[href*="followers"]')
        if not follower:
            BaseClass.logger.debug(u'话题关注人数未找到')
        self.info['follower'] = follower[0].get_text()
        return

    def parse_description(self):
        description = self.dom.select('#zh-fav-head-description-source')
        if not description:
            BaseClass.logger.debug(u'话题描述未找到')
        self.info['description'] = self.get_tag_content(description[0])
        return

    def parse_comment_count(self):
        comment = self.dom.select('#zh-list-meta-wrap  a[name="addcomment"]')
        if not comment:
            self.info['comment'] = self.match_int(comment[0].get_text())
        return


class BaseParser(ParserTools):
    def __init__(self, content):
        self.dom = BeautifulSoup(content, 'html.parser')
        self.answer_parser = SimpleAnswer()

    def get_answer_dom_list(self):
        return self.dom.select('.zm-item-answer')

    def get_answer_list(self):
        answer_list = []
        for dom in self.get_answer_dom_list():
            self.answer_parser.set_dom(dom)
            answer_list.append(self.answer_parser.get_info())
        return answer_list

    def get_question_dom_list(self):
        return self.dom.select('div.zm-item')

    def get_question_info_list(self):
        question_info_list = []
        parser = SimpleQuestion()
        for dom in self.get_question_dom_list():
            parser.set_dom(dom)
            question_info_list.append(parser.get_info())
        return question_info_list

    def get_extra_info(self):
        """
        扩展功能：获取扩展信息
        需重载
        """
        return

class AuthorParser(BaseParser):
    def get_extra_info(self):
        author = AuthorInfo(self.dom)
        return author.get_info()

class TopicParser(AuthorParser):
    def get_question_dom_list(self):
        return self.dom.select('div.content')

    def get_answer_dom_list(self):
        return self.dom.select('div.content')

    def get_extra_info(self):
        topic = TopicInfo(self.dom)
        return topic.get_info()

class CollectionParser(AuthorParser):
    def get_answer_dom_list(self):
        return self.dom.select('div.zm-item')

    def get_extra_info(self):
        collection = CollectionInfo(self.dom)
        return collection.get_info()

class QuestionParser(BaseParser):
    def __init__(self, content):
        self.dom = BeautifulSoup(content, 'html.parser')
        self.answer_parser = Answer()

    def get_question_info_list(self):
        parser = QuestionInfo()
        parser.set_dom(self.dom)
        return [parser.get_info()]