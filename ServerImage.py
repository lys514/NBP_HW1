from api_sender import *
from base_auth_info import *
from ServerSetting import *

def createMemberServerImage(instNo, serverImageNo="None", memberServerImageName="None",
                             memberServerImageDescription="None"):
    '''
    funcDescription: 회원의 서버이미지를 생성합니다.
    :param instNo: 생성할 서버이미지에 해당하는 Inst
    :param serverImageNo: 이미지를 생성할 대상이 되는 서버 인스턴스 번호 ( 중지/운영중 상태의 서버만 가능합니다. )
    :param memberServerImageName: 생성할 회원 서버 이미지명
    :param memberServerImageDescription: 생성할 회원 서버 이미지에 대한 설명
    '''

    response2 = getServerImageList2(serverImageNo=serverImageNo)
    if response2 != None:
        print("기존 서버 이미지 불러옴")
        return response2

    url = "/server/v2/createMemberServerImage"
    params = {
        "serverInstanceNo": instNo,
        "memberServerImageName": memberServerImageName,
        "memberServerImageDescription": memberServerImageDescription
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["createMemberServerImageResponse"]["memberServerImageList"][0]

def getServerImageList(image):
    '''
    funcDescription: 회원의 서버이미지 리스트를 조회합니다.
    :param image: 조회할 회원 서버 이미지 번호 리스트
    '''

    url = "/server/v2/getMemberServerImageList"
    serverImageNo = image["memberServerImageNo"]
    regionNo = image["region"]["regionNo"]
    params = {
        "memberServerImageNoList.1": serverImageNo,
        "regionNo": regionNo
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["getMemberServerImageListResponse"]["memberServerImageList"][0]

def checkServerImage(inst, max_retry, sleep_time, statusName):
    '''
    funcDescription: 서버 이미지 상태를 확인합니다.
    :param inst: 서버 이미지 리스트
    :param max_retry: 최대 시도 횟수
    :param sleep_time: 대기 시간
    :param statusName: 서버 이미지 상태 ( created )
    '''

    for i in range(max_retry):
        response = getServerImageList(inst)

        code = response["memberServerImageStatusName"]
        if code != statusName:
            time.sleep(sleep_time)
        else:
            return True
    return False

def createInstanceByImage(serverProductCode, imageServerName, serverImageNo, regionNo, zoneNo):
    '''
    funcDescription: 서버 이미지를 사용하여 서버 인스턴스(VM)를 생성합니다.
    :param serverProductCode: 생성할 서버 이미지를 결정하기 위한 서버이미지 상품코드
    :param imageServerName: 생성할 서버 이미지 이름 ( 서버 재사용 위함)
    :param serverImageNo: 사용할 서버 이미지 번호
    :param regionNo: 서버가 생성될 REGIONNO
    :param zoneNo: 서버가 생성될 ZONENO
    '''

    response2 = getServerPreInstance(imageServerName, regionNo, zoneNo)
    if response2 != None:
        print("기존 복제한 서버 불러옴")
        return response2

    url = "/server/v2/createServerInstances"
    params = {
        "serverProductCode": serverProductCode,
        "memberServerImageNo": serverImageNo,
        "regionNo": regionNo,
        "zoneNo": zoneNo
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["createServerInstancesResponse"]["serverInstanceList"][0]

def getServerImageList2(serverImageNo):
    '''
    funcDescription: 회원의 서버이미지 리스트를 조회합니다. ( 생성된 서버 이미지 재사용하기 위함 )
    :param serverImageNo: 조회할 서버 이미지 넘버
    '''

    url = "/server/v2/getMemberServerImageList"
    params = {
        "memberServerImageNoList.1": serverImageNo
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    if response["getMemberServerImageListResponse"]["totalRows"] != 0:
        return response["getMemberServerImageListResponse"]["memberServerImageList"][0]
    else:
        return None
