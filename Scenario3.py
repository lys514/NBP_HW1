from api_sender import *
from base_auth_info import *
from PortForwarding import *
from ServerSetting import *

import os.path as path
import sys
import base64
import time
import threading
import crypto

sys.modules['Crypto'] = crypto # import Crypto error 해결하기 위함
from Crypto.PublicKey import RSA
from Crypto import Random

if __name__ == "__main__":
    # SSD,HDD 디스크 타입 검색
    imageProductCode = getImageProductCode()
    productCode_inst1 = getProductCode(imageProductCode, "STAND", "SSD")
    productCode_inst2 = getProductCode(imageProductCode, "STAND", "HDD")

    instLoginKeyName = ["instkey1", "instkey2"]
    instLoginKey = list()

    for keyName in instLoginKeyName:
        # 처음 서버 만들때
        if findLoginKeyList(keyName) == False:
            print("로그인키 새로 생성함")
            instTmpLoginKey = createLoginKey(keyName)
            # PrivateKey 포맷 따르기 위해 pem으로 저장
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
        print("키 재사용함")
        with open(pubAccessKeyPath, "r", encoding='utf-8') as pubFile:
            publicKey = pubFile.read()

        with open(prvAccessKeyPath, "r", encoding='utf-8') as prvFile:
            privateKey = prvFile.read()

    '''
    PukeyAuthentication yes
    AuthorizedKeyFile .ssh/ authorized_keys
    -> ~/.ssh/authorized_keys에 publicKey 추가해야 서버 로그인가능
    
    init_script -> shell에서 처음 실행시킬 명령어 저장 (publicKey setting)
    '''
    init_script = "#!/bin/bash\nmkdir ~/.ssh\ncat >> ~/.ssh/authorized_keys\n" + publicKey + "\n"
    print("init_script 정보")
    print(init_script)
    print("=====================================================================")

    # 2. 서버 생성 시 상기 init-script 실행되게 설정
    inst1 = createServerInstance(imageProductCode, productCode_inst1, "s16c3899ede2", instLoginKeyName[0], 1, 2, init_script)
    inst2 = createServerInstance(imageProductCode, productCode_inst2, "s16c3899f66d", instLoginKeyName[1], 1, 3, init_script)

    inst1_No = inst1["serverInstanceNo"]
    inst2_No = inst2["serverInstanceNo"]
    instList = [inst1_No, inst2_No]

    changeServerStatus(instList, 'start')
    print("서버 실행중")
    waitforServer(instList, checkStatusByNo, 'running')
    print("서버 실행 완료")
    print("=====================================================================")

    print("Root Password 정보")
    password1 = getRootPassword(inst1_No, privateKey=instLoginKey[0])
    password2 = getRootPassword(inst2_No, privateKey=instLoginKey[1])
    print("server1 의 password : ", password1)
    print("server2 의 password : ", password2)
    print("=====================================================================")

    print("Port Forwarding 정보")
    # 3. 포트 포워딩을 통해 SSH command로 hostname 변경
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

    # https://ujuc.github.io/2014/04/07/python-paramiko/
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # HostKey 받아서 저장 -> 처음ssh 접근할때 yes누르는 작업
    print("SSH Command 설정중")
    # 첫번째 서버
    ssh.connect(hostname=forwardIp1, username="root", password=password1, port=externalPort1)
    ssh.exec_command("hostnamectl set-hostname modifiedserver1")
    stdin1, stdout1, stderr1 = ssh.exec_command("hostnamectl status") # get_pty -> script 실행하면서 출력하기 위함
    serverinfo1 = stdout1.read().decode("utf-8")
    ssh.close()

    # 두번째 서버
    ssh.connect(hostname=forwardIp2, username="root", password=password2, port=externalPort2)
    ssh.exec_command("hostnamectl set-hostname modifiedserver2")
    stdin2, stdout2, stderr2 = ssh.exec_command("hostnamectl status")  # get_pty -> script 실행하면서 출력하기 위함
    serverinfo2 = stdout2.read().decode("utf-8")

    print("변경된 서버 정보")
    print("ServerInfo : ", serverinfo1)

    ssh.close()
    print("=====================================================================")

    changeServerStatus(instList, 'reboot')
    print("서버 리부팅하는 중")
    waitforServer(instList, checkStatusByNo, 'running')
    print("서버 리부팅 완료")
    print("=====================================================================")

    # (2) 서버 정지
    changeServerStatus(instList, 'stop')
    print("서버 정지하는 중")
    waitforServer(instList, checkStatusByNo, 'stopped')
    print("서버 정지 완료")
    print("=====================================================================")
    time.sleep(5)

    # (3) 서버 시작
    changeServerStatus(instList, 'start')
    print("서버 다시 시작하는 중")
    waitforServer(instList, checkStatusByNo, 'running')
    print("서버 다시 시작 완료")
    print("=====================================================================")

    # (4) 서버 정지
    changeServerStatus(instList, 'stop')
    print("서버 다시 정지하는 중")
    waitforServer(instList, checkStatusByNo, 'stopped')
    print("서버 다시 정지 완료")
    print("=====================================================================")
    time.sleep(5)

    # 5. 상기 두 서버 동시 반납
    print("서버 반납하는 중")
    changeServerStatus(instList, 'terminate')
    print("서버 반납 완료")
    print("=====================================================================")
