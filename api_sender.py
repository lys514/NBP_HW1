import hashlib
import hmac
import base64
import time
import urllib.parse # 인코딩 모듈
import urllib.request
import ssl
import json
import requests
import paramiko

class APISender:

    def __init__(self, base_auth_info):
        self.access_key = base_auth_info.get_access_key()
        self.access_secret = base_auth_info.get_access_secret()
        self.url = base_auth_info.get_url()
        self.req_path = base_auth_info.get_req_path()

    # 시나리오2의 새로운 request -> URL인코딩 필요(유효한 아스키코드로 바꿔서 서버와 통신하기 위함)
    def request(self, path, headers=dict(), params=dict(), isJson=True):
        # 로그인을 위한 세션 할당
        sess = requests.Session()
        # 입력받은 헤더 추가 -> 어차피 밑에서만 추가함
        sess.headers.update(headers)

        # 특수문자 -> 문자열 변환(공백을 "+"로 바꾼다)
        args = [urllib.parse.quote_plus(str(k)) + "=" + urllib.parse.quote_plus(str(v)) for k, v in params.items()]
        #print("args : ", args)
        path = path + "?" + "&".join(args)
        #print("full_path : ", path)

        if isJson is True:
            path += "&responseFormatType=JSON"

        #signature
        timestamp = str(int(time.time() * 1000))
        sign = self.make_signature(timestamp, ep_path=path)

        # header
        default_header_key = ['x-ncp-apigw-timestamp', 'x-ncp-iam-access-key', 'x-ncp-apigw-signature-v2']
        default_header_value = [timestamp, self.access_key, sign]
        default_headers = dict(zip(default_header_key, default_header_value))

        sess.headers.update(default_headers)

        result = sess.get("https://ncloud.apigw.ntruss.com" + path)

        return json.loads(result.content)

    def make_signature(self, timestamp, ep_path):
        access_secret_bytes = bytes(self.access_secret, 'UTF-8')

        method = "GET"
        #ep_path = self.req_path

        message = method + " " + ep_path + "\n" + timestamp + "\n" + self.access_key
        '''
        GET /server/v2/~
        timestamp
        access_key    
        '''
        message = bytes(message, 'UTF-8')
        singing_key = base64.b64encode(hmac.new(access_secret_bytes, message, digestmod=hashlib.sha256).digest())

        return singing_key
