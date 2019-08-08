from api_sender import *
from base_auth_info import *
from PortForwarding import *
from ServerSetting import *
from PublicIpSetting import *
from LoadBalancer import *

import os.path as path
import sys
import base64
import inspect
import requests
import time
import threading
import crypto

sys.modules['Crypto'] = crypto  # ToDo : import crypto 해결
from Crypto.PublicKey import RSA
from Crypto import Random

if __name__ == "__main__":
    # SSD,HDD 디스크 타입 검색
    imageProductCode = getImageProductCode()
    productCode_inst1 = getProductCode(imageProductCode, "STAND", "SSD")
    productCode_inst2 = getProductCode(imageProductCode, "STAND", "HDD")
    productCodeList = [productCode_inst1, productCode_inst2]

    instLoginKeyName = ["instkey1", "instkey2"]
    instLoginKey = list()

    for keyName in instLoginKeyName:
        # 처음 서버 만들때
        if findLoginKeyList(keyName) == False:
            print("로그인키 새로 생성함")
            instTmpLoginKey = createLoginKey(keyName)
            loginkeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제' + '/Scenario2' + keyName + '.pem'
            with open(loginkeyPath, "w", encoding="utf-8") as f:
                f.write(instTmpLoginKey)
        # 기존 서버 쉽게 활용하기 위함
        else:
            print("기존 로그인키 활용함")
            loginkeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제' + '/Scenario2' + keyName + '.pem'
            with open(loginkeyPath, "r", encoding="utf-8") as f:
                instTmpLoginKey = f.read()

        instLoginKey.append(instTmpLoginKey)
    print("=====================================================================")

    ##################################################################################
    # 1. 서버 생성 전에 SSH key 설정하는 init-script 등록
    accessKeyName = "instAccessKey"
    pubAccessKeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제' + '/Scenario3' + accessKeyName + '.pub'
    prvAccessKeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제' + '/Scenario3' + accessKeyName + '.prv'

    # 처음 Key Pair 생성할 때
    if not path.isfile(pubAccessKeyPath) or not path.isfile(prvAccessKeyPath):
        print("처음 키페어 생성함")
        '''
        키를 2048비트로 생성
        메시지를 publicKey로 암호화 -> publickey().export_key()
        암호화된 메시지를 privateKey로 복호화 -> export_key()
        '''
        KEY_LENGTH = 2048
        random_generator = Random.new().read
        tmpKeypair = RSA.generate(KEY_LENGTH, random_generator)

        key_pair = [tmpKeypair.publickey().export_key(format="OpenSSH"), tmpKeypair.export_key()]
        publicKey = key_pair[0].decode('utf-8')
        privateKey = key_pair[1].decode('utf-8')

        with open(pubAccessKeyPath, "w", encoding='utf-8') as pubFile:
            pubFile.write(publicKey)

        with open(prvAccessKeyPath, "w", encoding='utf-8') as prvFile:
            prvFile.write(privateKey)

    # 그 후 키 재사용 할때
    else:
        print("키페어 재사용함")
        with open(pubAccessKeyPath, "r", encoding='utf-8') as pubFile:
            publicKey = pubFile.read()


        with open(prvAccessKeyPath, "r", encoding='utf-8') as prvFile:
            privateKey = prvFile.read()

    '''
    PubkeyAuthentication yes
    AuthorizedKeyFile .ssh/ authorized_keys
    -> ~/.ssh/authorized_keys에 publicKey 추가해야 서버 로그인가능
    '''

    # 1. 서버 생성 후 apache 서버 설정
    init_script = '''
        #!/bin/bash
        mkdir ~/.ssh/
        echo {} >> ~/.ssh/authorized_keys
        yum -y install httpd
        systemctl enable httpd
        systemctl start httpd
        echo `hostname` >> /var/www/html/index.html
    '''.format(publicKey)

    init_script = inspect.cleandoc(init_script)
    print("init_script : ", init_script)
    print("=====================================================================")


    # 2. 서버 생성 시 상기 init-script 실행되게 설정
    serverName = ["s16c37378e97", "s16c37379564"]
    inst1 = createServerInstance(imageProductCode, productCode_inst1, serverName[0], instLoginKeyName[0], 1, 2,
                                 init_script)
    inst2 = createServerInstance(imageProductCode, productCode_inst2, serverName[1], instLoginKeyName[1], 1, 3,
                                 init_script)

    inst1_No = inst1["serverInstanceNo"]
    inst2_No = inst2["serverInstanceNo"]
    instNoList = [inst1_No, inst2_No]

    changeServerStatus(instNoList, 'start')
    print("서버 실행중")
    waitforServer(instNoList, checkStatusByNo, 'running')
    print("서버 실행 완료")
    print("=====================================================================")

    print("Root Password 정보")
    password1 = getRootPassword(inst1_No, privateKey=instLoginKey[0])
    password2 = getRootPassword(inst2_No, privateKey=instLoginKey[1])
    print("server1 의 password : ", password1)
    print("server2 의 password : ", password2)
    print("=====================================================================")

    print("Port Forwarding 정보")
    externalPort1 = 6000
    externalPort2 = 7000
    internalPort = 22

    print("포트포워딩 시작")

    rule1 = addPortForwardingRules(inst1, externalPort1, internalPort)
    forwardIp1 = rule1["portForwardingPublicIp"]
    print(inst1["serverName"] + "포워딩 IP : ", forwardIp1)

    rule2 = addPortForwardingRules(inst2, externalPort2, internalPort)
    forwardIp2 = rule2["portForwardingRuleList"][0]["serverInstance"]["portForwardingPublicIp"]
    print(inst2["serverName"] + "포워딩 IP : ", forwardIp2)

    print("모든 서버 포트포워딩 완료")
    print("=====================================================================")

    # 공인 IP 추가
    publicIps = list()
    # 첫번째 서버 공인 IP 할당
    response1 = getPublicIpInstanceList(serverInstName=serverName[0], regionNo=1, zoneNo=2)
    if (response1 == None):
        print("Server1 공인 IP 처음 할당")
        response1 = createPublicIpInstance(instNoList[0], regionNo=1, zoneNo=2, description="Server1 Public IP")
        publicIps.append(response1["publicIp"])
    else:
        print("Server1 할당된 공인 IP 사용")
        publicIps.append(response1["publicIp"])

    # 두번째 서버 공인 IP 할당
    response2 = getPublicIpInstanceList(serverInstName=serverName[1], regionNo=1, zoneNo=3)
    if (response2 == None):
        print("Server2 공인 IP 처음 할당")
        response2 = createPublicIpInstance(instNoList[1], regionNo=1, zoneNo=3, description="Server2 Public IP")
        publicIps.append(response2["publicIp"])
    else:
        print("Server2 할당된 공인 IP 사용")
        publicIps.append(response2["publicIp"])

    print("Server1 공인 IP : ", publicIps[0])
    print("Server2 공인 IP : ", publicIps[1])
    print("=====================================================================")

    tmpResponse1 = requests.get("http://" + publicIps[0])
    tmpResponse2 = requests.get("http://" + publicIps[1])
    print("Server1 apache 연결확인 : ", tmpResponse1.text.splitlines()[:1])
    print("Server2 apache 연결확인 : ", tmpResponse2.text.splitlines()[:1])
    print("=====================================================================")


    # 2. 상기 두 서버를 바인드하는 로드밸런서 생성
    lbInstance = createLoadBalancerInstance(instNoList, "HTTP", 80, 80, "/index.html", "InstLB", "SIPHS", "scenario9 LB")
    lbInstanceNo = lbInstance["loadBalancerInstanceNo"]
    lbDomainName = lbInstance["domainName"]
    print("로드 밸런서 실행까지 대기중")
    time.sleep(60)
    print("로드 밸런서 실행 완료")
    print("=====================================================================")

    print("RR 알고리즘으로 변경 -> 상기 두 서버로 번갈아가며 요청")
    changeLoadBalancerAlogorithm(lbInstanceNo, "RR")
    # 3. HTTP 접속되는지 확인
    for i in range(1, 10):
        print(str(i) + "번째 접속 -> ", end='')
        result = requests.get("http://" + lbInstance["domainName"])
        time.sleep(1)
        tmp = result.content.decode("utf-8")[0:-1]
        print("접속 결과 : ", tmp)
    print("=====================================================================")

    print("SIPHS 알고리즘으로 변경 -> 상기 하나의 서버로 요청")
    changeLoadBalancerAlogorithm(lbInstanceNo, "SIPHS")
    # 3. HTTP 접속되는지 확인
    for i in range(1, 10):
        print(str(i) + "번째 접속 -> ", end='')
        result = requests.get("http://" + lbInstance["domainName"])
        time.sleep(1)
        tmp = result.content.decode("utf-8")[0:-1]
        print("접속 결과 : ", tmp)
    print("=====================================================================")
