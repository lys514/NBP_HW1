from api_sender import *
from base_auth_info import *
from BlockStorage import *
from ServerImage import *
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
    PukeyAuthentication yes
    AuthorizedKeyFile .ssh/ authorized_keys
    -> ~/.ssh/authorized_keys에 publicKey 추가해야 서버 로그인가능

    init_script -> shell에서 처음 실행시킬 명령어 저장 (publicKey setting)
    '''

    init_script = "#!/bin/bash\nmkdir ~/.ssh\ncat >> ~/.ssh/authorized_keys\n" + publicKey + "\n"
    print("=====================================================================")

    # 2. 서버 생성 시 상기 init-script 실행되게 설정
    serverName = ["s16c38d4b427", "s16c38d4bb53"]
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

    # 1. 서버 생성 후 추가 스토리지 생성
    # 추가 스토리지 생성하려면 서버 running 될때 까지 대기 (waitforServer에서 처리하지만 3~5초 정도 딜레이 있음)
    print("추가 스토리지 생성 중")
    storage1 = createBlockStorageInstances(instNoList[0], 50, diskDetailTypeCode="SSD")
    storage2 = createBlockStorageInstances(instNoList[1], 50, diskDetailTypeCode="HDD")
    storageList = [storage1, storage2]

    storage1_No = storage1["blockStorageInstanceNo"]
    storage2_No = storage2["blockStorageInstanceNo"]
    storageNoList = [storage1_No, storage2_No]
    print("storageNo : ", storageNoList)
    print("추가 스토리지 생성 완료")
    waitforServer(storageList, checkBlockStorageInstanceByNo, 'attached')
    print("=====================================================================")

    #  서버 패스워드 획득 -> Authentication Failed error
    print("Root Password 정보")
    password1 = getRootPassword(inst1_No, privateKey=instLoginKey[0])
    password2 = getRootPassword(inst2_No, privateKey=instLoginKey[1])
    print("server1 의 password : ", password1)
    print("server2 의 password : ", password2)
    print("=====================================================================")

    ################################################################################

    # 3. 포트 포워딩을 통해 SSH command로 hostname 변경
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

    # 2. SSH command로 file-system make
    # https://ujuc.github.io/2014/04/07/python-paramiko/
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # HostKey 받아서 저장 -> 처음ssh 접근할때 yes누르는 작업
    print("SSH Command 설정중")
    # 첫번째 서버
    ssh.connect(hostname=forwardIp1, username="root", password=password1, port=externalPort1)
    # exec_command -> 세션별로 명령어 전달하기 때문에
    # 파티션 할당하는 명령어에서 연속적인 처리 못함
    # shell 유지하는 send_shell함수 참조함
    open_shell = ssh.invoke_shell()
    command = [
        "fdisk -l\n", "fdisk /dev/xvdb\n", "n\n", "p\n", "\n", "\n", "\n", "w\n",
        "mkfs.xfs /dev/xvdb1\n",
        "mkdir /mnt/new_disk\n",
        "mount /dev/xvdb1 /mnt/new_disk\n",
        "df -k\n"
    ]
    for i in range(len(command)):
        open_shell.send(command[i])
        time.sleep(2)
        if i == len(command)-1:
            print("Server1 File-system 정보")
            print_shell(open_shell)
    ssh.close()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 두번째 서버
    ssh.connect(hostname=forwardIp2, username="root", password=password2, port=externalPort2)
    open_shell = ssh.invoke_shell()
    command = [
        "fdisk -l\n", "fdisk /dev/xvdb\n", "n\n", "p\n", "\n", "\n", "\n", "w\n",
        "mkfs.xfs /dev/xvdb1\n",
        "mkdir /mnt/new_disk\n",
        "mount /dev/xvdb1 /mnt/new_disk\n",
        "df -k\n"
    ]
    for i in range(len(command)):
        open_shell.send(command[i])
        time.sleep(2)
        if i == len(command) - 1:
            print("Server2 File-system 정보")
            print_shell(open_shell)

    ssh.close()
    print("=====================================================================")

    # 1. 상기 KR-1 서버 한 대 정지
    print("상기 KR-1 서버 정지 시작")
    changeServerStatus(instNoList[0], 'stop')
    waitforServer([instNoList[0]], checkStatusByNo, 'stopped')
    print("상기 KR-1 서버 정지 완료")
    print("=====================================================================")

    # 2. 내 서버이미지 생성 요청
    print("서버 이미지 요청 시작")
    response = createMemberServerImange(instNoList[0])
    print("서버 이미지 요청 결과 : ", response)
    print("=====================================================================")

    # 3. 요청 후 1분 뒤 서버 시작
    print("1분 대기 시작")
    time.sleep(60)
    print("=====================================================================")

    print("상기 KR-1 서버 재시작")
    changeServerStatus(instNoList[0], 'start')
    waitforServer([instNoList[0]], checkStatusByNo, 'running')
    print("상기 KR-1 서버 재시작 완료")
    print("=====================================================================")
