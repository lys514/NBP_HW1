from api_sender import *
from base_auth_info import *
from BlockStorage import *
from ServerImage import *
from PortForwarding import *
from ServerSetting import *

import os.path as path
import sys
import time
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
        # 로그인키 처음 만들때
        if findLoginKeyList(keyName) == False:
            print("로그인키 새로 생성함")
            instTmpLoginKey = createLoginKey(keyName)
            # PrivateKey 포맷 따르기 위해 pem으로 저장
            loginkeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제' + '/Scenario2' + keyName + '.pem'
            with open(loginkeyPath, "w", encoding="utf-8") as f:
                f.write(instTmpLoginKey)
        # 기존 로그인키 사용할때
        else:
            print("기존 로그인키 활용함")
            loginkeyPath = path.expanduser('~') + '/PycharmProjects' + '/1차과제' + '/Scenario2' + keyName + '.pem'
            with open(loginkeyPath, "r", encoding="utf-8") as f:
                instTmpLoginKey = f.read()

        instLoginKey.append(instTmpLoginKey)
    print("=====================================================================")

    ###############################################################################################
    # 시나리오 3번 시작
    # 1. 서버 생성 전에 SSH key 설정하는 init-script 등록
    # SSH Key 생성 후 저장 -> 계속 사용하기 위함
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

    init_script -> publicKey setting ( SSH Key 로 로그인 하기 위함 )
    '''

    init_script = '#!/bin/bash \n mkdir ~/.ssh/ \n echo "' + publicKey + '" >> ~/.ssh/authorized_keys'
    print("=====================================================================")

    # 2. 서버 생성 시 상기 init-script 실행되게 설정
    serverName = ["s16c40456d83", "s16c404574dd"]
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

    ###############################################################################################
    # 시나리오 4번 시작
    # 1. 서버 생성 후 추가 스토리지 생성
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

    # 2. SSH command로 file-system make
    # https://ujuc.github.io/2014/04/07/python-paramiko/
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # HostKey 받아서 저장 -> 처음ssh 접근할때 yes누르는 작업
    print("SSH Command 설정중")
    # 첫번째 서버
    ssh.connect(hostname=forwardIp1, username="root", password=password1, port=externalPort1)
    # ToDo : command 전달 후 sleep하는 부분 exec_commad 로 해결완료
    open_shell = ssh.invoke_shell()
    command = [
        "fdisk -l\n", "fdisk /dev/xvdb\n", "n\n", "p\n", "\n", "\n", "\n", "w\n",
        "mkfs.xfs /dev/xvdb1\n",
        "mkdir /mnt/new_disk\n",
        "mount /dev/xvdb1 /mnt/new_disk\n",
        "df -k\n"
    ]
    for i in range(len(command)):
        stdin, stdout, stderr = ssh.exec_command(command[i])
        # http://docs.paramiko.org/en/latest/api/file.html#paramiko.file.BufferedFile.write
        stdin.write("\n")
        stdin.flush()
        if i == len(command) - 1:
            print("Server1 File-system 정보")
            print(str(stdout.readlines()))

    # for i in range(len(command)):
    #     open_shell.send(command[i])
    #     time.sleep(2)
    #     if i == len(command) - 1:
    #         print("Server1 File-system 정보")
    #         print_shell(open_shell)
    # ssh.close()

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
        stdin, stdout, stderr = ssh.exec_command(command[i])
        # http://docs.paramiko.org/en/latest/api/file.html#paramiko.file.BufferedFile.write
        stdin.write("\n")
        stdin.flush()
        if i == len(command) - 1:
            print("Server2 File-system 정보")
            print(str(stdout.readlines()))

    # for i in range(len(command)):
    #     open_shell.send(command[i])
    #     time.sleep(2)
    #     if i == len(command) - 1:
    #         print("Server2 File-system 정보")
    #         print_shell(open_shell)

    ssh.close()
    print("=====================================================================")

    ###############################################################################################
    # 시나리오 6번 시작
    # 1. 상기 KR-1 서버 한 대 정지
    print("상기 KR-1 서버 정지 시작")
    changeServerStatus(instNoList[0], 'stop')
    waitforServer([instNoList[0]], checkStatusByNo, 'stopped')
    print("상기 KR-1 서버 정지 완료")
    print("=====================================================================")


    # 2. 내 서버이미지 생성 요청
    print("서버 이미지 요청 시작")
    serverImage = createMemberServerImage(instNoList[0], serverImageNo="23258")
    print("서버 이미지 요청 결과 : ", serverImage)
    print("=====================================================================")

    # 3. 요청 후 1분 뒤 서버 시작
    print("1분 대기 시작(서버 이미지 복제중)")
    time.sleep(60)
    print("=====================================================================")

    print("상기 KR-1 서버 재시작")
    changeServerStatus(instNoList[0], 'start')
    waitforServer([instNoList[0]], checkStatusByNo, 'running')
    print("상기 KR-1 서버 재시작 완료")
    print("=====================================================================")

    print("서버 이미지 생성까지 대기 시작")
    waitforServer([serverImage], checkServerImage, 'created')
    print("서버 이미지 생성 완료")
    print("=====================================================================")

    ###############################################################################################
    # 시나리오 7번 시작
    # 1. 내 서버 이미지로부터 서버를 KR-1에 생성
    # 2. 내 서버 이미지로부터 서버를 KR-2에 생성
    print("내 서버 이미지로부터 서버를 KR-1,2에 생성")
    serverImageNo = serverImage["memberServerImageNo"]
    imageServerName = ["s16c40529589", "s16c40529e98"]
    imageInst1 = createInstanceByImage(productCodeList[0], imageServerName[0], serverImageNo, 1, 2)
    imageInst2 = createInstanceByImage(productCodeList[1], imageServerName[1], serverImageNo, 1, 3)
    imageInstNoList = [imageInst1["serverInstanceNo"], imageInst2["serverInstanceNo"]]

    print("이미지 인스턴스 모두 생성될때까지 대기")
    waitforServer(imageInstNoList, checkStatusByNo, "running")
    print("이미지 인스턴스 모두 생성 완료")
    print("=====================================================================")

    # 2-1. 새로 생성한 서버 포트포워딩
    print("Port Forwarding 정보")
    externalPort3 = 6001
    externalPort4 = 7001
    internalPort = 22

    print("이미지서버 포트포워딩 시작")

    rule3 = addPortForwardingRules(imageInst1, externalPort3, internalPort)
    forwardIp3 = rule3["portForwardingPublicIp"]
    print(imageServerName[0] + "포워딩 IP : ", forwardIp3)

    rule4 = addPortForwardingRules(imageInst2, externalPort4, internalPort)
    forwardIp4 = rule4["portForwardingRuleList"][0]["serverInstance"]["portForwardingPublicIp"]
    print(imageServerName[1] + "포워딩 IP : ", forwardIp4)

    print("모든 이미지 서버 포트포워딩 완료")
    print("=====================================================================")

    # 3. SSH key로 접속 가능한지 확인
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # HostKey 받아서 저장 -> 처음ssh 접근할때 yes누르는 작업

    # pkey객체 만들어서 ssh_key로 연결 -> ACG 세팅문제 해결(6001, 7001 포트 추가)
    myKey = paramiko.RSAKey.from_private_key_file(prvAccessKeyPath)

    print("SSH PrivatetKey 전달해서 서버 연결 확인")
    # 세번째 서버연결 테스트
    print("내 서버 이미지로부터 생성된 첫번째 서버 연결 확인중")
    try:
        ssh.connect(hostname=forwardIp3, username="root", pkey=myKey, port=externalPort3)
        print("첫번째 이미지 서버 연결 가능")
    except (Exception, ConnectionResetError) as e:
        print("첫번째 이미지 서버 연결 불가능")

    # 네번째 서버연결 테스트
    print("내 서버 이미지로부터 생성된 두번째 서버 연결 확인중")
    try:
        ssh.connect(hostname=forwardIp4, username="root", pkey=myKey, port=externalPort4)
        print("두번째 이미지 서버 연결 가능")
    except (Exception, ConnectionResetError) as e:
        print("두번째 이미지 서버 연결 불가능")
    ssh.close()
    print("=====================================================================")
