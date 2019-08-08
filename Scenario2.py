from base_auth_info import *
from api_sender import *
from ServerSetting import *
from PortForwarding import *

import os.path as path
import time
import threading


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
            loginkeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제'+ '/Scenario2'+ keyName + '.pem'
            with open(loginkeyPath, "w", encoding="utf-8") as f:
                f.write(instTmpLoginKey)
        # 기존 서버 쉽게 활용하기 위함
        else:
            print("기존 키 활용함")
            loginkeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제'+ '/Scenario2'+ keyName + '.pem'
            with open(loginkeyPath, "r", encoding="utf-8") as f:
                instTmpLoginKey = f.read()

        instLoginKey.append(instTmpLoginKey)
    print("=====================================================================")

    # 1. 서버 생성 후 port forwarding 설정
    inst1 = createServerInstance(imageProductCode, productCode_inst1, "s16c384fdf1e", instLoginKeyName[0], 1, 2)
    inst2 = createServerInstance(imageProductCode, productCode_inst2, "s16c384fe7bb", instLoginKeyName[1], 1, 3)
    
    inst1_No = inst1["serverInstanceNo"]
    inst2_No = inst2["serverInstanceNo"]
    instList = [inst1_No, inst2_No]

    changeServerStatus(instList, 'start')
    print("서버 실행중")
    waitforServer(instList, checkStatusByNo, 'running')
    print("서버 실행 완료")
    print("=====================================================================")
    time.sleep(30)

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

    # 2. 서버 패스워드 획득 -> Authentication Failed error
    password1 = getRootPassword(inst1_No, privateKey=instLoginKey[0])
    password2 = getRootPassword(inst2_No, privateKey=instLoginKey[1])
    print("server1 의 password : ", password1)
    print("server2 의 password : ", password2)
    print("=====================================================================")

    # 3. 서버 로그인해서 hostname 정보 획득
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # HostKey 받아서 저장 -> 처음ssh 접근할때 yes누르는 작업

    # 첫번째 서버
    ssh.connect(hostname=forwardIp1, username="root", password=password1, port=externalPort1)
    stdin1, stdout1, stderr1 = ssh.exec_command("hostname", get_pty=True)
    hostname1 = stdout1.read().decode("utf-8")
    print("Hostname1 : ", hostname1)

    # 두번째 서버 -> forwardIp 할당 제대로 해야 hostname 접근가능
    ssh.connect(hostname=forwardIp2, username="root", password=password2, port=externalPort2)
    stdin2, stdout2, stderr2 = ssh.exec_command("hostname", get_pty=True)
    hostname2 = stdout2.read().decode("utf-8")
    print("Hostname2 : ", hostname2)

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
