import requests
import json
from time import sleep
import os

class LeetcodeSpider():
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'origin': 'https://leetcode-cn.com'
    }

    def __init__(self) -> None:
        self.session = requests.Session()
        self.is_login = False
        self.csrftoken = ''

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
            print("Login successfully!")
            self.is_login = True
            return True
        else:
            print("Login failed!")
            return False

    def getsubmissions(self) -> None:
        """获得提交记录"""
        submissions_url = 'https://leetcode-cn.com/api/submissions/'

        if not self.is_login:
            print("Please Login First")
            return

        self.submissions = list()
        submission_names = set()

        cnt = 0

        while True:
            rep = self.session.get(
                submissions_url, params={'offset': cnt})
            if not rep.ok:
                break
            rep_json = json.loads(rep.content.decode('utf-8'))

            cnt += len(rep_json['submissions_dump'])

            for submission in rep_json['submissions_dump']:
                if submission['title'] not in submission_names and submission['status_display'] == 'Accepted':
                    submission_names.add(submission['title'])
                    self.submissions.append({
                        'id': submission['id'],
                        'title': submission['title'],
                        'url': submission['url']
                    })
            if not rep_json['has_next']:
                break
            sleep(1)
        print(f"共获取到{len(self.submissions)}条AC记录")

    def getcodes(self, dir: str):
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
        os.mkdir(dir)
        os.chdir(dir)
        for submission in self.submissions:
            
            data['variables']['id'] = submission['id']
            req = self.session.post("https://leetcode-cn.com/graphql/", data=json.dumps(data), headers=headers)
            if not req.ok:
                return
            req_json = json.loads(req.content.decode('utf-8'))['data']['submissionDetail']
            try:
                with open(req_json['question']['titleSlug'] + '.py', 'w') as f:
                    f.write(req_json['code'])
            except:
                print(f"获取{submission['title']}出错啦！")
                continue
            print(f"获取{submission['title']}")
            sleep(1)