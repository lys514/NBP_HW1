from api_sender import *
from base_auth_info import *
from ServerSetting import *

import threading

def getImageProductCode():
    '''
    funcDescription: 네이버 클라우드 플랫폼에서 제공하는 서버이미지 상품리스트를 조회합니다.
    '''

    url = "/server/v2/getServerImageProductList"
    base_auth_info = BaseAuthInfo()
    params = {"platformTypeCodeList.1": "LNX64"}
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["getServerImageProductListResponse"]["productList"][0]["productCode"]

def getProductCode(imageProductCode, serverType, diskType='SSD'):
    '''
    funcDescription: 네이버 클라우드 플랫폼에서 제공하는 서버스펙 상품리스트를 조회합니다.
    :param imageProductCode: 서버이미지 상품코드
    :param serverType: 서버 타입
    :param diskType: 디스크 타입
    '''

    url = "/server/v2/getServerProductList"
    base_auth_info = BaseAuthInfo()
    params = {"serverImageProductCode": imageProductCode}
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    productList = response['getServerProductListResponse']['productList']
    for product in productList:
        # 서버 타입 확인
        if product['productType']['code'] == serverType:
            # 디스크 타입 SSD
            if diskType == "SSD" and diskType in product['productName']:
                return product['productCode']
            # 디스크 타입 HDD
            elif diskType == "HDD":
                return product['productCode']

    # return None ->                         

def createLoginKey(keyName):
    '''
    funcDescription: 서버인스턴스(VM)에 접속시 로그인키를 이용하여 비밀번호를 암호화하고 복호화하는 키를 생성합니다.
    :param keyName: 생성할 키 이름 ( 이미 생성된 키명이 존재할 경우 오류가 발생됩니다. )
    '''

    url = "/server/v2/createLoginKey"
    base_auth_info = BaseAuthInfo()
    params = {'keyName': keyName}
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response['createLoginKeyResponse']['privateKey']

def deleteLoginKey(keyName):
    '''
    funcDescription: 서버인스턴스(VM)에 접속시 로그인키를 이용하여 비밀번호를 암호화하고 복호화하는 키를 삭제합니다.
    :param keyName: 삭제할 키 이름
    '''

    url = "/server/v2/deleteLoginKey"
    base_auth_info = BaseAuthInfo()
    params = {'keyName': keyName}
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response['deleteLoginKeyResponse']['returnMessage']

def createServerInstance(imageProductCode, productCode, serverName, loginKey, regionNo, zoneNo, userData):
    '''
    funcDescription: 서버 인스턴스(VM)를 생성합니다.
    :param imageProductCode: 생성할 서버 이미지를 결정하기 위한 서버이미지 상품코드
    :param productCode: 생성할 서버스펙을 결정하기 위한 서버스펙 상품코드
    :param serverName: 생성할 서버명
    :param loginKey: 공개키로 암호화 시킬 로그인키명
    :param regionNo: 서버가 생성될 REGIONNO
    :param zoneNo: 서버가 생성될 ZONENO
    :param userData: 서버가 최초 부팅시 사용자가 설정한 사용자 데이터 스크립트 수행 ( init_script )
                     userData값을 넣기전에 base64 Encoding, URL Encoding 반드시 필요
                     base64로 Encoding된 결과를 다시 URL Encoding을 하지 않으면 signature invalid error
    '''

    response2 = getServerPreInstance(serverName, regionNo, zoneNo)
    if response2 != None:
        print("기존 서버 불러옴")
        return response2

    url = "/server/v2/createServerInstances"
    base_auth_info = BaseAuthInfo()
    params = {
        "serverImageProductCode": imageProductCode,
        "serverProductCode": productCode,
        "loginKeyName": loginKey,
        "regionNo": regionNo,
        "zoneNo": zoneNo,
        "userData": base64.b64encode(userData.encode('utf-8')).decode('utf-8')
    }
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    try:
        product = response['createServerInstancesResponse']['serverInstanceList'][0]
    except KeyError:
        return None
    return product

def getServerPreInstance(instName, regionNo, zoneNo):
    '''
    funcDescription: 서버 인스턴스(VM) 리스트를 조회합니다.
    :param instName: 조회할 인스턴스 이름
    :param regionNo: 서버 리스트가 조회될 리전(Region)
    :param zoneNo: 서버 리스트가 조회될 존(zone)
    '''

    url = "/server/v2/getServerInstanceList"
    params = {
        "searchFilterName ": "serverName",
        'searchFilterValue': instName,
        'regionNo': regionNo,
        'zoneNo': zoneNo
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    if response['getServerInstanceListResponse']['totalRows'] != 0:
        if response['getServerInstanceListResponse']['serverInstanceList'][0]['serverName'] == instName:
            return response['getServerInstanceListResponse']['serverInstanceList'][0]
        else:
            return response['getServerInstanceListResponse']['serverInstanceList'][1]
    else:
        return None

def waitforServer(instList, target, statusName):
    '''
    funcDescription: 서버 인스턴스, 서버 이미지, 서버 이미지 인스턴스 등의 특정 상태까지 대기한다.
    :param instList: 서버 인스턴스 리스트 ,서버 이미지 리스트, 서버 이미지 인스턴스 리스트
    :param target: 각 인스턴스의 상태를 체크할 함수
    :param statusName: 각 인스턴스의 체크할 상태
    '''

    sleep_time = 15
    max_retry = 100

    # 동시에 action 수행하기 위해 threads를 저장
    # https://oss.navercorp.com/2019-Ncloud-Intern-Program/jun-su.kim/blob/scenario4/serverController.py
    threads = []
    for inst in instList:
        thread = threading.Thread(target=target, args=(inst, max_retry, sleep_time, statusName))
        threads.append(thread)

    # 저장해둔 threads를 한번에 모두 실행하고, 모두 완료까지 대기
    for thread in threads:
        # print("{} is start ".format(threading.currentThread().getName()))
        thread.start()
    for thread in threads:
        thread.join()

def changeServerStatus(instList, status):
    '''
    funcDescription: 각 인스턴스의 상태를 변경한다.
    :param instList: 상태를 변경할 인스턴스 리스트
    :param action: 변경할 상태
    '''

    url = ""
    if status == "start":
        url = "/server/v2/startServerInstances"
    elif status == "stop":
        url = "/server/v2/stopServerInstances"
    elif status == "reboot":
        url = "/server/v2/rebootServerInstances"
    elif status == "terminate":
        url = "/server/v2/terminateServerInstances"

    # 서버 한개만 필요할 때
    if isinstance(instList, str):
        params = {"serverInstanceNoList.1": instList}
    else:
        params = dict()
        for i in range(len(instList)):
            params["serverInstanceNoList." + str(i + 1)] = instList[i]

    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    req.request(url, params=params)

def checkStatusByNo(instNo, max_retry, sleep_time, statusName):
    '''
    funcDescription: 서버 인스턴스의 상태를 체크하여 원하는 상태까지 대기합니다. ( waitforServer에서 사용하기 위함 )
    :param instNo: 상태체크할 서버 인스턴스의 번호
    :param max_retry: 최대 시도 횟수
    :param sleep_time: 대기 시간
    :param statusName: 체크할 서버 상태
    '''

    url = "/server/v2/getServerInstanceList"
    params = {"serverInstanceNoList.1": instNo}

    for i in range(max_retry):
        base_auth_info = BaseAuthInfo()
        req = APISender(base_auth_info)
        response = req.request(url, params=params)
        tmp = response['getServerInstanceListResponse']['serverInstanceList'][0]['serverInstanceStatusName']

        if tmp != statusName:
            time.sleep(sleep_time)
        else:
            return True

    return False

def getRootPassword(inst_No, privateKey=""):
    '''
    funcDescription: 서버(VM)의 로그인키로 root 계정의 비밀번호를 조회합니다.
                     privateKey를 설정하지 않으면 해당 인스턴스의 공개키를 조회합니다.
    :param inst_No: 조회할 서버 인스턴스 번호
    :param privateKey: 서버의 로그인키(인증키)
    '''

    url = "/server/v2/getRootPassword"
    params = {
        "serverInstanceNo": inst_No,
        "privateKey": privateKey
    }

    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["getRootPasswordResponse"]["rootPassword"]

def findLoginKeyList(keyName):
    '''
    funcDescription: 서버인스턴스(VM)에 접속시 로그인키를 이용하여 비밀번호를 암호화하고 복호화하는 키를 조회합니다.
    :param keyname: 조회할 키 명
    '''

    url = "/server/v2/getLoginKeyList"
    params = {
        "keyName": keyName
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    if response['getLoginKeyListResponse']['totalRows'] == 0:  # 처음 생성하는 키인경우
        return False
    else:  # 기존 키가 존재하는 경우
        return True

def print_shell(open_shell):
    '''
    funcDescription: ssh로 command를 전달한 결과를 그대로 출력한다.
    # ToDo : command 전달하고 시간 지연문제 -> exec.command로 해결 ( stdin.write + stdin.flush )
    :param open_shell: ssh.invoke_shell()
    '''

    stdout, stderr = "", ""
    while open_shell.recv_ready():
        stdout += open_shell.recv(1024).decode('utf-8')

    while open_shell.recv_stderr_ready():
        stderr += open_shell.recv_stderr(1024).decode('utf-8')

    if stdout:
        print("결과값 : ", stdout)
    else:
        print("결과값 : ", stderr)
    del stdout, stderr
