class BaseAuthInfo:
    def __init__(self):
        self.access_key = "w7rZqyPPbxPqxPres43H"
        self.access_secret = "8mQ4I0LHRvWndTZdwL79REyzA0Ufv33FzLbZc3Ci"
        # ToDo : req_path, url 함수별로 각 각 사용
        self.req_path = "/server/v2/getServerImageProductList?platformTypeCodeList.1=LNX64"
        self.url = 'https://ncloud.apigw.ntruss.com'

    def get_access_key(self):
        return self.access_key

    def get_access_secret(self):
        return self.access_secret

    def get_req_path(self):
        return self.req_path

    def get_url(self):
        return self.url
