from logging import log
import requests
import json
from time import sleep
import os
import logging

class LeetcodeSpider():
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'origin': 'https://leetcode-cn.com'
    }

    def __init__(self, *, submission_file='submission.json', log_level = logging.INFO) -> None:
        self.session = requests.Session()
        self.is_login = False
        self.csrftoken = ''
        self.submission_file = submission_file
        logging.basicConfig(level=log_level, format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    def login(self, email: str, password: str) -> bool:
        """登录账号"""
        login_url = 'https://leetcode-cn.com/accounts/login/'
        login_data = {
            'login': email,
            'password': password
        }

        self.session.post(login_url, headers=self.headers, data=login_data)

        is_login = self.session.cookies.get('LEETCODE_SESSION') != None
        if is_login:
            logging.info("登录成功")
            self.is_login = True
            return True
        else:
            logging.error("登录失败")
            return False

    def getsubmissions(self) -> None:
        """获得提交记录"""
        submissions_url = 'https://leetcode-cn.com/api/submissions/'

        if not self.is_login:
            print("Please Login First")
            return

        self.submissions = list()
        submission_names = set()
        start_timestamp = 0
        prev_submissions = list()

        try:
            with open(self.submission_file, 'r') as f:
                prev_submissions = json.load(f)
            start_timestamp = prev_submissions[0]['timestamp']
        except FileNotFoundError or IndexError:
            logging.info(f'创建{self.submission_file}')

        cnt = 0

        logging.info('开始获取提交记录')

        while True:
            rep = self.session.get(
                submissions_url, params={'offset': cnt})
            if not rep.ok:
                break
            rep_json = json.loads(rep.content.decode('utf-8'))

            cnt += len(rep_json['submissions_dump'])
            time_flag = False
            for submission in rep_json['submissions_dump']:
                if submission['timestamp'] <= start_timestamp:
                    time_flag = True
                    break
                if submission['title'] not in submission_names and submission['status_display'] == 'Accepted':
                    submission_names.add(submission['title'])
                    self.submissions.append({
                        'id': submission['id'],
                        'title': submission['title'],
                        'url': submission['url'],
                        'timestamp': submission['timestamp']
                    })
            logging.debug(f'获取到{len(self.submissions)}条记录')
            if not rep_json['has_next'] or time_flag:
                break
            sleep(1)
        
        with open(self.submission_file, 'w') as f:
            submissions = prev_submissions + self.submissions
            submissions.sort(key=lambda x: x['timestamp'], reverse=True)
            json.dump(submissions, f)
        logging.info(f"共获取到{len(self.submissions)}条AC记录")

    def getcodes(self, dir: str):
        """下载代码"""
        self.session.get("https://leetcode-cn.com")
        csrftoken = ''
        for cookie in self.session.cookies:
            if cookie.name == 'csrftoken':
                csrftoken = cookie.value
        data = {
                    "operationName": "mySubmissionDetail",
                    "variables": { "id": "123652466" },
                    "query":
                    """
                    query mySubmissionDetail($id: ID!) {
                        submissionDetail(submissionId: $id) {
                            id
                            code
                            runtime
                            memory
                            rawMemory
                            statusDisplay
                            timestamp
                            lang
                            passedTestCaseCnt
                            totalTestCaseCnt
                            sourceUrl
                            question {
                                titleSlug
                                title
                                translatedTitle
                                questionId
                                __typename
                            }
                            ... on GeneralSubmissionNode {
                                outputDetail {
                                    codeOutput
                                    expectedOutput
                                    input
                                    compileError
                                    runtimeError
                                    lastTestcase
                                    __typename
                                }
                            __typename
                            }
                        __typename
                        }
                    }"""
            }
        headers = {
            'origin': 'https://leetcode-cn.com',
            'x-csrftoken': csrftoken,
            'x-definition-name': 'submissionDetail',
            'x-operation-name': 'mySubmissionDetail',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
            'x-timezone': 'Asia/Shanghai',
            'Content-Type': 'application/json'
        }
        logging.debug(f'创建{dir}目录')
        try:
            os.mkdir(dir)
        except FileExistsError:
            logging.debug(f'{dir}目录已经存在')
        os.chdir(dir)
        for i, submission in enumerate(self.submissions):
            
            data['variables']['id'] = submission['id']
            req = self.session.post("https://leetcode-cn.com/graphql/", data=json.dumps(data), headers=headers)
            if not req.ok:
                return
            req_json = json.loads(req.content.decode('utf-8'))['data']['submissionDetail']
            try:
                lang = req_json['lang']
                m = {
                    'python3': '.py',
                    'python2': '.py',
                    'java': '.java',
                    'c++': '.cpp',
                    'javascript': '.js',
                    'c': '.c',
                }
                with open(req_json['question']['titleSlug'] + m[lang], 'w') as f:
                    f.write(req_json['code'])
            except:
                logging.warning(f"获取{submission['title']}出错啦！")
                continue
            logging.info(f"获取{submission['title']} {(i+1)/len(self.submissions)}")
            sleep(1)