class HostedZoneConfig(object):
    def __init__(self):
        self.description = None
        self.registered_domain = None


class DatacenterConfig(object):
    def __init__(self):
        self.vpc = None
        self.internet_gateway = None
        self.route_table = None
        self.subnets = []
        self.security_groups = []
        self.instances = []


class VpcConfig(object):
    def __init__(self):
        self.name = None
        self.description = None
        self.cidr = None
        self.region = None
        self.tags = []


class InternetGatewayConfig(object):
    def __init__(self):
        self.name = None
        self.tags = []


class RouteTableConfig(object):
    def __init__(self):
        self.name = None
        self.tags = []


class SubnetConfig(object):
    def __init__(self):
        self.name = None
        self.description = None
        self.az = None
        self.cidr = None
        self.tags = []


class SecurityGroupConfig(object):
    def __init__(self):
        self.name = None
        self.description = None
        self.rules = []
        self.tags = []


class CidrRuleConfig(object):
    def __init__(self):
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.cidr = None
        self.description = None


class SgpRuleConfig(object):
    def __init__(self):
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.sgp_name = None
        self.description = None


class InstanceConfig(object):
    def __init__(self):
        self.name = None
        self.username = None
        self.password = None
        self.private_ip = None
        self.security_group = None
        self.subnet = None
        self.parent_img = None
        self.target_img = None
        self.dns_domain = None
        self.host_name = None
        self.tags = []


class TagConfig(object):
    def __init__(self):
        self.key = None
        self.value = None
