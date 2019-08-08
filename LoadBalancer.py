from api_sender import *
from base_auth_info import *
from ServerSetting import *

def createLoadBalancerInstance(instNoList, protocol, lbPort, serverPort, healthChk=None, lbName=None, lbAlgorithm='RR', lbDescription=None):
    '''
    funcDescription: 로드밸런서 인스턴스를 생성합니다.
    :param instNoList: 바인딩할 서버의 번호 리스트
    :param protocol: 로드밸런서 RULE에 추가할 프로토콜구분코드
    :param lbPort: 로드밸런서 RULE에 추가할 로드밸런서 포트
    :param serverPort: 로드밸런서 RULE에 추가할 서버 포트
    :param healthChk: 로드밸런서 RULE의 헬스 체크 경로
    :param lbName: 생성할 로드밸런서명
    :param lbAlgorithm: 로드밸런서알고리즘구분코드 ( RR, LC, SIPHS 입력 가능 )
    :param lbDescription: 로드밸런서설명
    '''
    
    url = "/loadbalancer/v2/createLoadBalancerInstance"
    params = {
        "createLoadBalancerInstance": lbName,
        "loadBalancerAlgorithmTypeCode": lbAlgorithm,
        "loadBalancerDescription": lbDescription,
        "loadBalancerRuleList.1.protocolTypeCode": protocol,
        "loadBalancerRuleList.1.loadBalancerPort": lbPort,
        "loadBalancerRuleList.1.serverPort": serverPort
    }

    if healthChk != None:
        params["loadBalancerRuleList.1.l7HealthCheckPath"] = healthChk

    # 두 서버 바인딩
    for i in range(len(instNoList)):
        params["serverInstanceNoList." + str(i+1)] = instNoList[i]

    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["createLoadBalancerInstanceResponse"]["loadBalancerInstanceList"][0]

def changeLoadBalancerAlogorithm(lbInstNo, lbAlgorithm):
    '''
    funcDescription: 로드밸런서인스턴스의 RULE 알고리즘 종류를 변경합니다.
    :param lbInstNo: 알고리즘 종류를 변경할 로드밸런서 인스턴스 번호
    :param lbAlgorithm: 변경할 알고리즘 종류
    '''
    
    url = "/loadbalancer/v2/changeLoadBalancerInstanceConfiguration"
    params = {
        "loadBalancerInstanceNo": lbInstNo,
        "loadBalancerAlgorithmTypeCode": lbAlgorithm,
        "loadBalancerRuleList.1.protocolTypeCode": "HTTP",
        "loadBalancerRuleList.1.loadBalancerPort": 80,
        "loadBalancerRuleList.1.serverPort": 80,
        "loadBalancerRuleList.1.l7HealthCheckPath": "/index.html"
    }
    base_auth_info = BaseAuthInfo()
    req = APISender(base_auth_info)
    response = req.request(url, params=params)

    return response["changeLoadBalancerInstanceConfigurationResponse"]["loadBalancerInstanceList"][0]
