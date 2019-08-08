from api_sender import *
from base_auth_info import *

def getPublicIpInstanceList(serverInstName=None, zoneNo=None, regionNo=None):
    '''
    funcDescription: 공인 IP 인스턴스 리스트를 조회합니다.
    :param serverInstName: 검색할 서버이름
    :param zoneNo: 공인 IP 인스턴스 리스트를 존(zone)을 이용해 필터링
    :param regionNo: 공인 IP 인스턴스 리스트를 리전(Region)을 이용해 필터링
    '''
    
    url = "/server/v2/getPublicIpInstanceList"
    params = {
        "searchFilterName": "associatedServerName",
        "searchFilterValue": serverInstName,
        "zoneNo": zoneNo,
        "regionNo": regionNo
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    # 처음 리스트에 아무것도 없을때
    if len(response["getPublicIpInstanceListResponse"]["publicIpInstanceList"]) == 0:
        return None

    return response["getPublicIpInstanceListResponse"]["publicIpInstanceList"][0]

def createPublicIpInstance(instNo, regionNo, zoneNo, description):
    '''
    funcDescription: 공인 IP 인스턴스를 생성합니다.
    :param instNo: 공인 IP를 생성 후 할당할 서버 인스턴스 번호
    :param regionNo: 공인 IP가 생설될 regionNo
    :param zoneNo: 공인 IP가 생성될 zoneNo
    :param description: 공인 IP 설명
    '''
    
    url = "/server/v2/createPublicIpInstance"
    params = {
        "serverInstanceNo": instNo,
        "regionNo": regionNo,
        "zoneNo": zoneNo,
        "publicIpDescription": description
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["createPublicIpInstanceResponse"]["publicIpInstanceList"][0]
