from urllib.parse import urljoin

from requestsutils import RequestsBase
from htmlutils import parse_document_from_requests

class V2EXError(Exception):
  pass

class V2EXFailure(V2EXError):
  def __init__(self, msg, req):
    self.msg = msg
    self.req = req

class NotLoggedIn(V2EXError):
  pass

class MissionNotAvailable(V2EXError):
  pass

class V2EX(RequestsBase):
  auto_referer = True
  userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0'

  index_url = 'https://www.v2ex.com/'
  login_url = 'https://www.v2ex.com/signin'
  daily_url = 'https://www.v2ex.com/mission/daily'

  def get_once_value(self):
    r = self.request(self.login_url)
    doc = parse_document_from_requests(r)
    return doc.xpath('//input[@name="once"]')[0].get('value')

  def login(self, username, password):
    once_value = self.get_once_value()
    post_data = {
      'next': '/',
      '101118e0072a431bff5935c20fb1dd87385aea4c2f1cd9b8fc523c04926eb19a': username,
      '15f8ca8aabad25a8b54b3e062233d59cb309d2b5fbaa1d6a6b99edc821a1ccd0': password,
      'once': once_value,
    }
    r = self.request(
      self.login_url, 'POST',
      data = post_data,
    )
    if '/signout?once=' not in r.text:
      raise V2EXFailure('login failed', r)

  def daily_mission(self):
    # may need this or mission will fail
    r = self.request(self.index_url)
    if '/signout?once=' not in r.text:
      raise NotLoggedIn

    r = self.request(self.daily_url)
    if 'href="/signin"' in r.text:
      raise NotLoggedIn

    doc = parse_document_from_requests(r)
    buttons = doc.xpath('//input[@value = "领取 X 铜币"]')
    if not buttons:
      raise MissionNotAvailable

    button = buttons[0]
    url = button.get('onclick').split("'")[1]
    r = self.request(urljoin(self.index_url, url))
    if '已成功领取每日登录奖励' not in r.text:
      raise V2EXFailure('daily mission failed', r)
