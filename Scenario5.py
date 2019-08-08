from api_sender import *
from base_auth_info import *
from PublicIpSetting import *
from PortForwarding import *
from ServerSetting import *

import os.path as path
import sys
import base64
import time
import threading
import crypto

sys.modules['Crypto'] = crypto  # import Crypto error 해결하기 위함
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
    print("=====================================================================")

    # 2. 서버 생성 시 상기 init-script 실행되게 설정
    serverName = ["s16c3c327dc7", "s16c3c3284f3"]
    inst1 = createServerInstance(imageProductCode, productCode_inst1, serverName[0], instLoginKeyName[0], 1, 2,
                                 init_script)
    inst2 = createServerInstance(imageProductCode, productCode_inst2, serverName[1], instLoginKeyName[1], 1, 3,
                                 init_script)

    inst1_No = inst1["serverInstanceNo"]
    inst2_No = inst2["serverInstanceNo"]
    instNoList = [inst1_No, inst2_No]
    instList = [inst1, inst2]

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

    ################################################################################
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

    # 1. 서버 생성 후 공인 아이피 allocate
    # 2. 생성된 공인 아이피 정보 획득
    # 3. 상기 두 서버에 공인 아이피 assign
    
    # 공인 IP 할당 여부 체크(처음에만 할당)
    publicIps = list()
    # 첫번째 서버 공인 IP 할당
    response1 = getPublicIpInstanceList(serverInstName=serverName[0], regionNo=1, zoneNo=2)
    if(response1 == None):
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

    # 4. 서버 B에 서버 A에서만 ssh command 가능하도록 xinetd 설정 변경
    print("SSH Command 설정중")
    srcPublicIp = publicIps[0]
    destPublicIp = publicIps[1]
    srcPortForwardingIp = forwardIp1
    destPortForwardingIp = forwardIp2

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=destPortForwardingIp, username="root", password=password2, port=externalPort2)
    open_shell = ssh.invoke_shell()

    open_shell.send("yum install xinetd\n")
    time.sleep(10)
    open_shell.send("y\n")
    time.sleep(5)
    open_shell.send("systemctl start xinetd\n")
    time.sleep(5)
    open_shell.send("echo sshd:" + srcPublicIp + ">> /etc/hosts.allow\n")
    time.sleep(5)
    open_shell.send("echo sshd: ALL >> /etc/hosts.deny\n")
    time.sleep(5)
    open_shell.send("service sshd restart\n")
    time.sleep(5)
    print("SSH Command 설정 완료")
    print("=====================================================================")
    print("이제 B는 A에서만 연결가능함")
    print("=====================================================================")
    ssh.close()

    # 5. 서버 B를 통해 서버 A로 ssh command되는지 확인
    print("B로 직접 연결 가능한지 Test 중")
    try:
        ssh.connect(hostname=destPortForwardingIp, username="root", password=password2, port=externalPort2)
        print("B로 직접 연결 가능")
    except (Exception, ConnectionResetError) as e:
        print("B로 직접 연결 불가능")
    ssh.close()

    print("A에서 B로 연결이 가능한지 Test 중")
    ssh.connect(hostname=srcPortForwardingIp, username="root", password=password1, port=externalPort1)
    stdin, stdout, stderr = ssh.exec_command("ssh root@" + destPortForwardingIp + "| echo $?")

    if stdout.read().decode("utf-8") == "0\n":
        print("A에서만 B 연결 가능")
    else:
        print("A에서 B 연결 불가능")
    ssh.close()
    print("=====================================================================")

    changeServerStatus(instNoList, 'reboot')
    print("서버 리부팅하는 중")
    waitforServer(instNoList, checkStatusByNo, 'running')
    print("서버 리부팅 완료")
    print("=====================================================================")

    # (2) 서버 정지
    changeServerStatus(instNoList, 'stop')
    print("서버 정지하는 중")
    waitforServer(instNoList, checkStatusByNo, 'stopped')
    print("서버 정지 완료")
    print("=====================================================================")

    # (3) 서버 시작
    changeServerStatus(instNoList, 'start')
    print("서버 다시 시작하는 중")
    waitforServer(instNoList, checkStatusByNo, 'running')
    print("서버 다시 시작 완료")
    print("=====================================================================")

    # (4) 서버 정지
    changeServerStatus(instNoList, 'stop')
    print("서버 다시 정지하는 중")
    waitforServer(instNoList, checkStatusByNo, 'stopped')
    print("서버 다시 정지 완료")
    print("=====================================================================")
