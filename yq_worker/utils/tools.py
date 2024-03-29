# encoding=utf8
import sys
import struct
from lxml import etree
from requests.adapters import HTTPAdapter
sys.path.append("..")
import re
import json
import configparser  # 读配置文件的
import codecs
import uuid
import urllib.parse
from urllib.parse import quote
from  yq_worker.utils.log import log
from tld import get_tld
from urllib import request, parse
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.proxy import ProxyType
import requests
import time
from bs4 import BeautifulSoup
from threading import Timer
import functools
import datetime
import time
import os
import sys
import execjs  # pip install PyExecJS
import hashlib
from pprint import pprint
from pprint import pformat
from bs4 import UnicodeDammit
from http.cookiejar import CookieJar as cj
import uuid
from hashlib import md5
import socket

TIME_OUT = 30
TIMER_TIME = 5
import traceback
def debug(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as err:
            traceback.print_exc()
    return wrapper

# 装饰器
def log_function_time(func):
    try:
        @functools.wraps(func)  # 将函数的原来属性付给新函数
        def calculate_time(*args, **kw):
            began_time = time.time()
            callfunc = func(*args, **kw)
            end_time = time.time()
            log.debug(func.__name__ + " run time  = " + str(end_time - began_time))
            return callfunc

        return calculate_time
    except:
        log.debug('求取时间无效 因为函数参数不符')
        return func


def run_safe_model(module_name):
    def inner_run_safe_model(func):
        try:
            @functools.wraps(func)  # 将函数的原来属性付给新函数
            def run_func(*args, **kw):
                callfunc = ''
                try:
                    callfunc = func(*args, **kw)
                except Exception as e:
                    log.error(module_name + ": " + func.__name__ + " - " + str(e))
                return callfunc

            return run_func
        except Exception as e:
            log.error(module_name + ": " + func.__name__ + " - " + str(e))
            return func

    return inner_run_safe_model


########################【网页解析相关】###############################
# ---------------------------自动处理编码 start -------------------------
FAIL_ENCODING = 'ISO-8859-1'

@debug
def get_unicode_html(html):
    if isinstance(html, str):
        return html

    if not html:
        return html

    converted = UnicodeDammit(html, is_html=True)
    if not converted.unicode_markup:
        raise Exception(
            'Failed to detect encoding of article HTML, tried: %s' %
            ', '.join(converted.tried_encodings))

    html = converted.unicode_markup
    return html


# @log_function_time

# -------------------------- 自动处理编码 end-----------------------------
# import chardet
@log_function_time
def get_html_by_urllib(url, code='utf-8', headers={}, proxies={}):
    html = None
    if not url.endswith('.exe') and not url.endswith('.EXE'):
        page = None
        is_timeout = False
        try:
            def timeout_handler(response):
                is_timeout = True
                if response:
                    response.close()

            if proxies:
                proxy_support = request.ProxyHandler(proxies)
                opener = request.build_opener(proxy_support)
                page = opener.open(quote(url, safe='/:?=&'), timeout=TIME_OUT)

            else:
                page = request.urlopen(quote(url, safe='/:?=&'), timeout=TIME_OUT)
            # 设置定时器 防止在read时卡死
            t = Timer(TIMER_TIME, timeout_handler, [page])
            t.start()
            # charset = chardet.detect(page.read())['encoding']
            html = page.read().decode(code, 'ignore')
            t.cancel()

        except Exception as e:
            log.error(e)
        finally:
            # page and page.close()
            if page and not is_timeout:
                page.close()

    return html and len(html) < 1024 * 1024 and html or None


@log_function_time
def get_html_by_webdirver(url, proxies=''):
    html = None
    try:

        driver = webdriver.PhantomJS()

        if proxies:
            proxy = webdriver.Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            proxy.http_proxy = proxies  # '220.248.229.45:3128'
            # 将代理设置添加到webdriver.DesiredCapabilities.PHANTOMJS中
            proxy.add_to_capabilities(webdriver.DesiredCapabilities.PHANTOMJS)
            driver.start_session(webdriver.DesiredCapabilities.PHANTOMJS)

        driver.get(url)
        html = driver.page_source
        # driver.save_screenshot('1.png')   #截图保存
        driver.close()
    except Exception as e:
        log.error(e)
    return html and len(html) < 1024 * 1024 and html or None


@debug
def get_html_by_requests(url, headers='', code='utf-8', data=None, proxies={},max_retries=1):
    html = None
    if not url.endswith('.exe') and not url.endswith('.EXE'):
        r = None
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=max_retries-1))
        s.mount('https://', HTTPAdapter(max_retries=max_retries-1))
        try:
            if data:
                r = s.post(url, headers=headers, timeout=TIME_OUT, data=data, proxies=proxies)
            else:
                r = s.get(url, headers=headers, timeout=TIME_OUT, proxies=proxies)

            if code:
                r.encoding = code
            html = r.text

        except Exception as e:
            log.error(e)
        finally:
            r and r.close()

    return html and len(html) < 1024 * 1024 and html or None, r
def get_json_by_requests(url, params=None, headers='', data=None, proxies={}):
    json = {}
    response = None
    try:
        # response = requests.get(url, params = params)
        if data:
            response = requests.post(url, headers=headers, data=data, params=params, timeout=TIME_OUT, proxies=proxies)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=TIME_OUT, proxies=proxies)
        response.encoding = 'utf-8'
        json = response.json()
    except Exception as e:
        log.error(e)
    finally:
        response and response.close()

    return json


def get_json_obj_by_requests(url, headers='', proxies={}):
    try:
        response = requests.get(url, headers=headers, timeout=TIME_OUT, proxies=proxies)
        response.encoding = 'utf-8'
        json_obj = json.loads(response.text)
    except Exception as e:
        log.error(e)

    return json_obj



def get_urls(html, stop_urls=['javascript', '+', '.css', '.js', '.rar', '.xls', '.exe', '.apk', '.doc', '.jpg', '.png',
                              '.flv', '.mp4']):
    # 不匹配javascript、 +、 # 这样的url
    regex = r'<a.*?href.*?=.*?["|\'](.*?)["|\']'

    urls = get_info(html, regex)
    urls = sorted(set(urls), key=urls.index)
    if stop_urls:
        stop_urls = isinstance(stop_urls, str) and [stop_urls] or stop_urls
        use_urls = []
        for url in urls:
            for stop_url in stop_urls:
                if stop_url in url:
                    break
            else:
                use_urls.append(url)

        urls = use_urls
    return urls


def get_full_url(root_url, sub_url):
    '''
    @summary: 得到完整的ur
    ---------
    @param root_url: 根url （网页的url）
    @param sub_url:  子url （带有相对路径的 可以拼接成完整的）
    ---------
    @result: 返回完整的url
    '''

    return urljoin(root_url, sub_url)


def joint_url(url, params):
    param_str = "?"
    for key, value in params.items():
        value = isinstance(value, str) and value or str(value)
        param_str += key + "=" + value + "&"

    return url + param_str[:-1]


def fit_url(urls, identis):
    identis = isinstance(identis, str) and [identis] or identis
    fit_urls = []
    for link in urls:
        for identi in identis:
            if identi in link:
                fit_urls.append(link)
    return list(set(fit_urls))


def get_param(url, key):
    params = url.split('?')[-1].split('&')
    for param in params:
        key_value = param.split('=', 1)
        if key == key_value[0]:
            return key_value[1]
    return None


def unquote_url(url):
    '''
    @summary: 将url解码
    ---------
    @param url:
    ---------
    @result:
    '''

    return urllib.parse.unquote(url)


def quote_url(url):
    '''
    @summary: 将url编码 编码意思http://www.w3school.com.cn/tags/html_ref_urlencode.html
    ---------
    @param url:
    ---------
    @result:
    '''

    return urllib.parse.quote(url)


_regexs = {}


# @log_function_time
def get_info(html, regexs, allow_repeat=False, fetch_one=False, split=None):
    regexs = isinstance(regexs, str) and [regexs] or regexs

    infos = []
    for regex in regexs:
        if regex == '':
            continue

        if regex not in _regexs.keys():
            _regexs[regex] = re.compile(regex, re.S | re.M)

        if fetch_one:
            infos = _regexs[regex].search(html)
            if infos:
                infos = infos.groups()
            else:
                continue
        else:
            infos = _regexs[regex].findall(str(html))

        if len(infos) > 0:
            # print(regex)
            break

    if fetch_one:
        infos = infos if infos else ('',)
        return infos if len(infos) > 1 else infos[0]
    else:
        infos = allow_repeat and infos or sorted(set(infos), key=infos.index)
        infos = split.join(infos) if split else infos
        return infos

# def get_domain(url):
#     domain = ''
#     try:
#         domain = get_tld(url)
#     except Exception as e:
#         log.debug(e)
#     return domain


def get_domain(url):
    try:
        proto, rest = urllib.parse.splittype(url)
        domain, rest = urllib.parse.splithost(rest)
        domain = domain[domain.find(".")+1:]
        return domain
    except Exception as e:
        return ''


def get_ip(domain):
    ip = socket.getaddrinfo(domain, 'http')[0][4][0]
    return ip


def get_localhost_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def ip_to_num(ip):
    ip_num = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])
    return ip_num


def get_tag(html, name=None, attrs={}, find_all=True):
    try:
        if html:
            soup = BeautifulSoup(html, "html.parser") if isinstance(html, str) else html
            result = soup.find_all(name, attrs) if find_all else soup.find(name, attrs)
            return result if result else []
        else:
            return []
    except Exception as e:
        log.error(e)
        return []


def get_text(soup, *args):
    try:
        return soup.get_text()
    except Exception as e:
        log.error(e)
        return ''


def del_html_tag(content, except_line_break=False, save_img=False):
    content = replace_str(content, '(?i)<script(.|\n)*?</script>')  # (?)忽略大小写
    content = replace_str(content, '(?i)<style(.|\n)*?</style>')
    content = replace_str(content, '<!--(.|\n)*?-->')
    content = replace_str(content, '(?!&[a-z]+=)&[a-z]+;?')  # 干掉&nbsp等无用的字符 但&xxx= 这种表示参数的除外
    if except_line_break:
        content = content.replace('</p>', '/p')
        content = replace_str(content, '<[^p].*?>')
        content = content.replace('/p', '</p>')
        content = replace_str(content, '[ \f\r\t\v]')

    elif save_img:
        content = replace_str(content, '(?!<img.+?>)<.+?>')  # 替换掉除图片外的其他标签
        content = replace_str(content, '(?! +)\s+', '\n')  # 保留空格
        content = content.strip()

    else:
        content = replace_str(content, '<(.|\n)*?>')
        content = replace_str(content, '\s')
        content = content.strip()

    return content


def del_html_js_css(content):
    content = replace_str(content, '(?i)<script(.|\n)*?</script>')  # (?)忽略大小写
    content = replace_str(content, '(?i)<style(.|\n)*?</style>')
    content = replace_str(content, '<!--(.|\n)*?-->')

    return content


def is_url(url):
    try:
        requests.get(url)
        return True
    except Exception as e:
        return False


def is_have_chinese(content):
    regex = '[\u4e00-\u9fa5]+'
    chinese_word = get_info(content, regex)
    return chinese_word and True or False


def is_have_english(content):
    regex = '[a-zA-Z]+'
    english_words = get_info(content, regex)
    return english_words and True or False


def get_chinese_word(content):
    regex = '[\u4e00-\u9fa5]+'
    chinese_word = get_info(content, regex)
    return chinese_word


def get_english_words(content):
    regex = '[a-zA-Z]+'
    english_words = get_info(content, regex)
    return english_words or ''


##################################################
def get_json(json_str):
    '''
    @summary: 取json对象
    ---------
    @param json_str: json格式的字符串
    ---------
    @result: 返回json对象
    '''

    try:
        return json.loads(json_str) if json_str else {}
    except Exception as e:
        log.error(e)
        return {}


def dumps_json(json_):
    '''
    @summary: 格式化json 用于打印
    ---------
    @param json_: json格式的字符串或json对象
    ---------
    @result: 格式化后的字符串
    '''
    try:
        if isinstance(json_, str):
            json_ = get_json(json_)

        json_ = json.dumps(json_, ensure_ascii=False, indent=4, skipkeys=True)

    except Exception as e:
        log.error(e)
        json_ = pformat(json_)

    return json_


def print(object):
    pprint(object)


def get_json_value(json_object, key):
    '''
    @summary:
    ---------
    @param json_object: json对象或json格式的字符串
    @param key: 建值 如果在多个层级目录下 可写 key1.key2  如{'key1':{'key2':3}}
    ---------
    @result: 返回对应的值，如果没有，返回''
    '''
    current_key = ''
    value = ''
    try:
        json_object = isinstance(json_object, str) and get_json(json_object) or json_object

        current_key = key.split('.')[0]
        value = json_object[current_key]

        key = key[key.find('.') + 1:]
    except Exception as e:
        return value

    if key == current_key:
        return value
    else:
        return get_json_value(value, key)


def to_chinese(unicode_str):
    format_str = json.loads('{"chinese":"%s"}' % unicode_str)
    return format_str['chinese']


##################################################
def replace_str(source_str, regex, replace_str=''):
    '''
    @summary: 替换字符串
    ---------
    @param source_str: 原字符串
    @param regex: 正则
    @param replace_str: 用什么来替换 默认为''
    ---------
    @result: 返回替换后的字符串
    '''
    str_info = re.compile(regex)
    return str_info.sub(replace_str, source_str)


##################################################
def get_conf_value(config_file, section, key):
    cp = configparser.ConfigParser(allow_no_value=True)
    with codecs.open(config_file, 'r', encoding='utf-8') as f:
        cp.read_file(f)
    return cp.get(section, key)


################################################
def capture(url, save_fn="capture.png"):
    directory = os.path.dirname(save_fn)
    mkdir(directory)

    browser = webdriver.PhantomJS()
    browser.set_window_size(1200, 900)
    browser.get(url)  # Load page
    # browser.execute_script("""
    #         (function () {
    #           var y = 0;
    #           var step = 100;
    #           window.scroll(0, 0);

    #           function f() {
    #             if (y < document.body.scroll_height) {
    #               y += step;
    #               window.scroll(0, y);
    #               set_timeout(f, 50);
    #             } else {
    #               window.scroll(0, 0);
    #               document.title += "scroll-done";
    #             }
    #           }

    #           set_timeout(f, 1000);
    #         })();
    #     """)

    # for i in range(30):
    #     if "scroll-done" in browser.title:
    #         break
    #     time.sleep(1)

    browser.save_screenshot(save_fn)
    browser.close()


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        pass


def write_file(filename, content, mode='w'):
    '''
    @summary: 写文件
    ---------
    @param filename: 文件名（有路径）
    @param content: 内容
    @param mode: 模式 w/w+ (覆盖/追加)
    ---------
    @result:
    '''

    directory = os.path.dirname(filename)
    mkdir(directory)
    with open(filename, mode, encoding='utf-8') as file:
        file.writelines(content)


def read_file(filename, readlines=False, encoding='utf-8'):
    '''
    @summary: 读文件
    ---------
    @param filename: 文件名（有路径）
    @param readlines: 按行读取 （默认False）
    ---------
    @result: 按行读取返回List，否则返回字符串
    '''

    content = ''
    try:
        with open(filename, 'r', encoding=encoding) as file:
            content = file.readlines() if readlines else file.read()
    except Exception as e:
        log.error(e)

    return content


def is_html(url):
    if not url:
        return False

    try:
        content_type = request.urlopen(url).info().get('Content-Type', '')

        if 'text/html' in content_type:
            return True
        else:
            return False
    except Exception as e:
        log.error(e)
        return False


def download_file(url, base_path, filename='', call_func=''):
    file_path = base_path + filename
    directory = os.path.dirname(file_path)
    mkdir(directory)

    # 进度条
    def progress_callfunc(blocknum, blocksize, totalsize):
        '''回调函数
        @blocknum : 已经下载的数据块
        @blocksize : 数据块的大小
        @totalsize: 远程文件的大小
        '''
        percent = 100.0 * blocknum * blocksize / totalsize
        if percent > 100:
            percent = 100
        # print ('进度条 %.2f%%' % percent, end = '\r')
        sys.stdout.write('进度条 %.2f%%' % percent + "\r")
        sys.stdout.flush()

    if url:
        try:
            log.debug('''
                         正在下载 %s
                         存储路径 %s
                      '''
                      % (url, file_path))

            request.urlretrieve(url, file_path, progress_callfunc)

            log.debug('''
                         下载完毕 %s
                         文件路径 %s
                      '''
                      % (url, file_path)
                      )

            call_func and call_func()
            return 1
        except Exception as e:
            log.error(e)
            return 0
    else:
        return 0


def get_file_list(path, ignore=[]):
    templist = path.split("*")
    path = templist[0]
    file_type = templist[1] if len(templist) >= 2 else ''

    # 递归遍历文件
    def get_file_list_(path, file_type, ignore, all_file=[]):
        file_list = os.listdir(path)

        for file_name in file_list:
            if file_name in ignore:
                continue

            file_path = os.path.join(path, file_name)
            if os.path.isdir(file_path):
                get_file_list_(file_path, file_type, ignore, all_file)
            else:
                if not file_type or file_name.endswith(file_type):
                    all_file.append(file_path)

        return all_file

    return get_file_list_(path, file_type, ignore) if os.path.isdir(path) else [path]


def rename_file(old_name, new_name):
    os.rename(old_name, new_name)


def del_file(path, ignore=[]):
    files = get_file_list(path, ignore)
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            log.error('''
                删除出错: %s
                Exception : %s
                ''' % (file, str(e))
                      )
        else:
            log.debug(file + " 删除成功")
        finally:
            pass


#############################################

def exec_js(js_code):
    '''
    @summary: 执行js代码
    ---------
    @param js_code: js代码
    ---------
    @result: 返回执行结果
    '''

    return execjs.eval(js_code)


def compile_js(js_func):
    '''
    @summary: 编译js函数
    ---------
    @param js_func:js函数
    ---------
    @result: 返回函数对象 调用 fun('js_funName', param1,param2)
    '''

    ctx = execjs.compile(js_func)
    return ctx.call


###############################################

def date_to_timestamp(date, time_format='%Y-%m-%d %H:%M:%S'):
    '''
    @summary:
    ---------
    @param date:将"2011-09-28 10:00:00"时间格式转化为时间戳
    @param format:时间格式
    ---------
    @result: 返回时间戳
    '''

    timestamp = time.mktime(time.strptime(date, time_format))
    return int(timestamp)


def timestamp_to_date(timestamp, time_format='%Y-%m-%d %H:%M:%S'):
    '''
    @summary:
    ---------
    @param timestamp: 将时间戳转化为日期
    @param format: 日期格式
    ---------
    @result: 返回日期
    '''

    date = time.localtime(timestamp)
    return time.strftime(time_format, date)


def get_current_timestamp():
    return int(time.time())


def get_current_date(date_format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.now().strftime(date_format)
    # return time.strftime(date_format, time.localtime(time.time()))


@run_safe_model('format_date')
def format_date(date, old_format='', new_format='%Y-%m-%d %H:%M:%S'):
    '''
    @summary: 格式化日期格式
    ---------
    @param date: 日期 eg：2017年4月17日 3时27分12秒
    @param old_format: 原来的日期格式 如 '%Y年%m月%d日 %H时%M分%S秒'
        %y 两位数的年份表示（00-99）
        %Y 四位数的年份表示（000-9999）
        %m 月份（01-12）
        %d 月内中的一天（0-31）
        %H 24小时制小时数（0-23）
        %I 12小时制小时数（01-12）
        %M 分钟数（00-59）
        %S 秒（00-59）
    @param new_format: 输出的日期格式
    ---------
    @result: 格式化后的日期，类型为字符串 如2017-4-17 3:27:12
    '''
    if not date:
        return ''

    if not old_format:
        regex = '(\d+)'
        numbers = get_info(date, regex, allow_repeat=True)
        formats = ['%Y', '%m', '%d', '%H', '%M', '%S']
        old_format = date
        for i, number in enumerate(numbers):
            if i == 0 and len(number) == 2:  # 年份可能是两位 用小%y
                old_format = old_format.replace(number, formats[i].lower(),
                                                1)  # 替换一次 '2017年11月30日 11:49' 防止替换11月时，替换11小时
            else:
                old_format = old_format.replace(number, formats[i], 1)  # 替换一次

    try:
        date_obj = datetime.datetime.strptime(date, old_format)
        date_str = datetime.datetime.strftime(date_obj, new_format)
    except Exception as e:
        log.error('日期格式化出错，old_format = %s 不符合 %s 格式' % (old_format, date))
        date_str = date
    return date_str


def delay_time(sleep_time=160):
    '''
    @summary: 睡眠  默认1分钟
    ---------
    @param sleep_time: 以秒为单位
    ---------
    @result:
    '''

    time.sleep(sleep_time)


def seconds_to_h_m_s(seconds):
    '''
    @summary: 将秒转为时分秒
    ---------
    @param seconds:
    ---------
    @result: 08:23:00
    '''

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    return '%02d:%02d:%02d' % (h, m, s)


################################################
def get_md5(source_str):
    m = hashlib.md5()
    m.update(source_str.encode('utf-8'))
    return m.hexdigest()


def get_sha1(*args):
    '''
    @summary: 获取唯一的32为值， 用于获取唯一的id
    ---------
    @param *args: 参与联合去重的值
    ---------
    @result:
    '''
    assert args, '参数不能为空'

    sha1 = hashlib.sha1()
    for arg in args:
        sha1.update(str(arg).encode())
    return sha1.hexdigest()


def get_base64(secret, message):
    '''
    @summary: 数字证书签名算法是："HMAC-SHA256"
              参考：https://www.jokecamp.com/blog/examples-of-creating-base64-hashes-using-hmac-sha256-in-different-languages/
    ---------
    @param secret: 秘钥
    @param message: 消息
    ---------
    @result: 签名输出类型是："base64"
    '''

    import hashlib
    import hmac
    import base64

    message = bytes(message, 'utf-8')
    secret = bytes(secret, 'utf-8')

    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature


def get_uuid(key1='', key2=''):
    '''
    @summary: 计算uuid值
    可用于将两个字符串组成唯一的值。如可将域名和新闻标题组成uuid，形成联合索引
    ---------
    @param key1:str
    @param key2:str
    ---------
    @result:
    '''

    uuid_object = ''

    if not key1 and not key2:
        uuid_object = uuid.uuid1()
    else:
        hash = md5(bytes(key1, "utf-8") + bytes(key2, "utf-8")).digest()
        uuid_object = uuid.UUID(bytes=hash[:16], version=3)

    return str(uuid_object)
@debug
def get_uuid2(key1='', key2='', key3=''):
    '''
    @summary: 计算uuid值
    可用于将两个字符串组成唯一的值。如可将域名和新闻标题组成uuid，形成联合索引
    ---------
    @param key1:str
    @param key2:str
    ---------
    @result:
    '''

    uuid_object = ''

    if not key1 and not key2 and not key3:
        uuid_object = uuid.uuid1()
    else:
        hash = md5(bytes(key1, "utf-8") + bytes(key2, "utf-8") + bytes(key3, "utf-8")).digest()
        uuid_object = uuid.UUID(bytes=hash[:16], version=3)
    return str(uuid_object)

def get_hash(text):
    return hash(text)


##################################################

def cut_string(text, length):
    '''
    @summary: 将文本按指定长度拆分
    ---------
    @param text: 文本
    @param length: 拆分长度
    ---------
    @result: 返回按指定长度拆分后形成的list
    '''

    text_list = re.findall('.{%d}' % length, text, re.S)
    leave_text = text[len(text_list) * length:]
    if leave_text:
        text_list.append(leave_text)

    return text_list


##################################################
def xpath_parser(html, regex, fetch_one=False):
    try:
        if fetch_one:
            e = etree.HTML(html)
            results = "".join(e.xpath(regex))
            return results
        else:
            e = etree.HTML(html)
            results = e.xpath(regex)
            return results
    except Exception as e:
        print(e)


def filter_useless_url(url):
    useless_keys = ["void(0)", "@", "app", "download", "passport", "javascript", "login", 'javascript', '+', '.css',
                    '.js', '.rar', '.xls', '.exe', '.apk', '.doc', '.jpg', '.png']
    for useless_key in useless_keys:
        if useless_key in url:
            return False
    return True



@debug
def get_url_domain(url):
    result = parse.urlparse(url)[1]
    try:
        domain=re.search(r"\.(.*)\.",result).group(1)
    except Exception as e:
        end=result.rfind(".")
        domain=result[:end]
    return domain

def url_detection(url, domain):
    try:
        response = requests.get(url)
        content_type = response.headers.get('Content-Type', '')
        code_type = response.status_code
        url = response.url
        html_text = response.text
        if domain not in url:
            return False
        if code_type != 200:
            return False
        if 'text/html' not in content_type and 'application/javascript' in content_type:
            return False
        if not html_text:
            return False
        return True
    except Exception as e:
        return False

def print_one_line(object):
    '''
    :param object:
    :return: 实时刷新在重控制台的输出。
    '''
    print(str(object))
    sys.stdout.write(str(object) + "\r")
    sys.stdout.flush()
def judge_url_contained(keyword,url):
    '''
    :param keyword: 域名
    :param url: 网站地址
    :return: 判断这个域名是否隶属于这个网站
    '''
    result = parse.urlparse(url)[1]
    try:
        domain=re.search(r"\.(.*)\.",result).group(1)
    except Exception as e:
        end=result.rfind(".")
        domain=result[:end]
    if "." in domain:
        str_list=domain.split(".")
        for domain in str_list:
            if keyword in domain:
                if len(keyword)==len(domain):
                    return True
                else:
                    return False
            else:
                continue
    else:
        if keyword in domain:
            if len(keyword)==len(domain):
                return True
            else:
                return False
        else:
            return False

@debug
def verfy_datetime(release_time_str):
    if release_time_str:
        release_time_str = format_date(release_time_str)
        #将字符串时间格式转换为datetime类型
        n_time = datetime.datetime.strptime(release_time_str, '%Y-%m-%d %H:%M:%S')
        # 范围时间
        d_time = datetime.datetime.strptime(str(datetime.datetime.now().date()) + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        # # 当前时间
        # d_time = datetime.datetime.now()
        # 判断当前时间是否在范围时间内
        if n_time < d_time:
            return str(n_time)

        else:
            return ""
    else:
        return ""
@debug
def replace_muti_str(info, need_replace={}):
    table = str.maketrans(need_replace)
    result = info.translate(table)
    return result
