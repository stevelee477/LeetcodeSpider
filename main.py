import logging
from LeetcodeSpider import LeetcodeSpider
from settings import EMAIL, PASSWORD, CODE_PATH

l = LeetcodeSpider()
l.login(EMAIL, PASSWORD)
l.getsubmissions()
l.getcodes(CODE_PATH)