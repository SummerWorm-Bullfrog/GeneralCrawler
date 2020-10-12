# *_*coding:utf-8 *_*
import yq_worker.utils.tools as tools
def get_video_info(html):
    regx1 = ' //div[@class="video_content"]//embed/@flashvars'
    result = tools.xpath_parser(html, regx1, fetch_one=True)
    if result:
        return True
    regx2 = '//source[@id="youth_video_src_1"]/@src'
    video_url = tools.xpath_parser(html, regx2, fetch_one=True)
    if video_url:
        return True
    regx3 = '//video/@src'
    video_url2 = tools.xpath_parser(html, regx3, fetch_one=True)
    if video_url2:
        return True

if __name__ == '__main__':
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
    }
    url = 'http://qclz.youth.cn/znl/201907/t20190725_12020476.htm'
    content = requests.get(url, headers=headers).text
    result = get_video_info(content)
    if result:
        print("我是视频哦")
