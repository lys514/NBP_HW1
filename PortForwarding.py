from api_sender import *
from base_auth_info import *
from ServerSetting import *

def getPortForwardingRuleList(inst):
    '''
    funcDescription: 포트포워딩 룰 리스트(Port Forwarding Rule List) 정보를 조회합니다.
                     최초에 서버를 생성하면, 계정당 하나씩 포트포워딩을 설정할 수 있는 공인 IP가 부여됩니다.
    :param inst: 포트포워딩 룰을 조회할 서버 인스턴스
    '''

    url = "/server/v2/getPortForwardingRuleList"
    params = {
        'regionNo': 1,
        'zoneNo': inst['zone']['zoneNo']
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)

    return req.request(url, params=params)


def addPortForwardingRules(inst, externalPort, internalPort):
    '''
    funcDescription: 포트포워딩 룰(Port Forwarding Rule)을 추가합니다.
                     보유한 서버에 포트포워딩 룰을 추가하여, 설정한 공인 IP와 포트(Port)로 접속할 수 있습니다.
    :param inst: 포트포워딩 룰 추가할 서버 인스턴스
    :param externalPort: 포트포워딩으로 접속할 외부 포트
    :param internalPort: 포트포워딩으로 접속할 내부 포트 [리눅스 : 22, 윈도우 : 3389]
    '''

    rules = getPortForwardingRuleList(inst)

    # 룰 추가 중복 방지(이미 추가한 경우)
    # if rules['getPortForwardingRuleListResponse']['totalRows'] != 0:
    #     print("기존 포트포워딩 사용")
    #     return rules['getPortForwardingRuleListResponse']

    rulesConfigureNo = rules['getPortForwardingRuleListResponse']['portForwardingConfigurationNo']
    instNo = inst["serverInstanceNo"]
    url = "/server/v2/addPortForwardingRules"
    params = {
        'portForwardingConfigurationNo': rulesConfigureNo,
        'portForwardingRuleList.1.serverInstanceNo': instNo,
        'portForwardingRuleList.1.portForwardingExternalPort': externalPort,
        'portForwardingRuleList.1.portForwardingInternalPort': internalPort,
    }

    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["addPortForwardingRulesResponse"]
