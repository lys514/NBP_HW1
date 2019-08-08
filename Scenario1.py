from api_sender import *
from base_auth_info import *
from ServerSetting import *

import os.path as path
import sys
import time

if __name__ == "__main__":
    # SSD,HDD 디스크 타입 검색
    imageProductCode = getImageProductCode()
    productCode_inst1 = getProductCode(imageProductCode, "STAND", "SSD")
    productCode_inst2 = getProductCode(imageProductCode, "STAND", "HDD")

    # 1. CentOS 7 표준 SSD 서버 KR-1에 생성
    # 2. CentOs 7 표준 HDD 서버 KR-2에 생성
    inst1 = createServerInstance(imageProductCode, productCode_inst1, 'instkey1', 1, 2)
    inst2 = createServerInstance(imageProductCode, productCode_inst2, 'instkey2', 1, 3)

    # print("inst1 : ", inst1)
    print("인스턴스 2개 생성 완료")
    print("=====================================================================")

    # 3. 두 서버의 아이피 주소 정보 획득 (server Object 함수 사용)
    inst1_ip = inst1["privateIp"]
    inst2_ip = inst2["privateIp"]
    print("첫 번째 서버의 ip : ", inst1_ip)
    print("두 번째 서버의 ip : ", inst2_ip)
    print("=====================================================================")

    inst1_No = inst1["serverInstanceNo"]
    inst2_No = inst2["serverInstanceNo"]
    instList = [inst1_No, inst2_No]


    print("running 상태까지 대기중")
    waitforServer(instList, checkStatusByNo, "running")
    print("running 상태 처리완료")
    print("=====================================================================")

    # 4. 상기 두 서버 동시에 리부팅 -> 정지 -> 시작 -> 정지
    '''
    각 서버 changeServerStatus로 상태 변경 한 후 
    (params = {"serverInstanceNoList.1": instList}를 통해서 상태 변경)
    waitforServer 함수에 접근해서 상태를 얻어
    thread 동시에 2개 처리한다
    '''
    # (1) 서버 리부팅
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

    # 5. 상기 두 서버 동시 반납
    print("서버 반납하는 중")
    changeServerStatus(instList, 'terminate')
    print("서버 반납 완료")
    print("=====================================================================")
