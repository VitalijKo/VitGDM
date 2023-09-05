import requests
from xml.etree import ElementTree
from ssdp import SSDP, Router


class PortMapping:
    def __init__(self,
                 remote_host='*',
                 public_port=0,
                 protocol='',
                 private_ip='',
                 private_port=0,
                 is_enabled=None,
                 description='',
                 lease_duration=-1
                 ):
        self.remote_host = remote_host
        self.public_port = public_port
        self.protocol = protocol
        self.private_ip = private_ip
        self.private_port = private_port
        self.is_enabled = is_enabled
        self.description = description
        self.lease_duration = lease_duration

    def __str__(self):
        return ' '.join([
            self.remote_host,
            self.public_port,
            self.protocol,
            self.private_ip,
            self.private_port,
            self.is_enabled,
            self.description,
            self.lease_duration
        ])

    @classmethod
    def parse_port_map_xml(cls, xml_text, router_type):
        doc = ElementTree.fromstring(xml_text)

        generic_portmap_tag_text = f'{{{router_type}}}GetGenericPortMappingEntryResponse'

        response_tag = doc[0][0]

        if response_tag.tag == generic_portmap_tag_text:
            remote_host = '*'
            public_port = 0
            protocol = ''
            private_ip = ''
            private_port = 0
            is_enabled = None
            description = ''
            lease_duration = -1

            for prop in response_tag:
                if prop.tag == 'NewRemoteHost':
                    remote_host = prop.text if prop.text else '*'

                elif prop.tag == 'NewExternalPort':
                    public_port = prop.text if prop.text else 0

                elif prop.tag == 'NewProtocol':
                    protocol = prop.text if prop.text else '-'

                elif prop.tag == 'NewInternalPort':
                    private_port = prop.text if prop.text else 0

                elif prop.tag == 'NewInternalClient':
                    private_ip = prop.text if prop.text else '*'

                elif prop.tag == 'NewEnabled':
                    is_enabled = prop.text if prop.text else '-'

                elif prop.tag == 'NewPortMappingDescription':
                    description = prop.text if prop.text else 'None'

                elif prop.tag == 'NewLeaseDuration':
                    lease_duration = prop.text if prop.text else '-'

            return PortMapping(
                remote_host=remote_host,
                public_port=public_port,
                protocol=protocol,
                private_ip=private_ip,
                private_port=private_port,
                is_enabled=is_enabled,
                description=description,
                lease_duration=lease_duration
            )


class UPnp:
    _add_port_mapping_template = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"><NewExternalPort>{}</NewExternalPort><NewProtocol>{}</NewProtocol><NewInternalPort>{}</NewInternalPort><NewInternalClient>{}</NewInternalClient><NewEnabled>1</NewEnabled><NewPortMappingDescription>{}</NewPortMappingDescription><NewLeaseDuration>0</NewLeaseDuration></u:AddPortMapping></s:Body></s:Envelope>'
    _delete_port_mapping_template = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:DeletePortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"><NewExternalPort>{}</NewExternalPort><NewProtocol>{}</NewProtocol></u:AddPortMapping></s:Body></s:Envelope>'
    _list_port_mappings_template = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:GetGenericPortMappingEntry xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"><NewPortMappingIndex>{}</NewPortMappingIndex></u:GetGenericPortMappingEntry></s:Body></s:Envelope>'

    @classmethod
    def add_port_mapping(cls, router_uuid, protocol, public_port, private_ip, private_port):
        print(f'Adding port mapping ({router_uuid}, {protocol}, {public_port}, {private_ip}, {private_port})')

        router = UPnp._find_router(router_uuid)

        if not router:
            print(f'No router found with uuid {router_uuid}')

            return

        url = f'{router.base_url}{router.control_url}'

        print(f'Adding port mapping ({private_ip} {private_port}/{protocol}) at {url}')

        headers = {
            'Host': f'{router.ip}:{router.port}',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPACTION': f'{router.type}#AddPortMapping'
        }

        mapping_description = f'dave_upnp_{private_ip}:{private_port}'

        data = UPnp._add_port_mapping_template.format(
            public_port,
            protocol,
            private_port,
            private_ip,
            mapping_description
        )

        response = requests.post(url, data=data, headers=headers)

        print(response.text)

    @classmethod
    def delete_port_mapping(cls, router_uuid, protocol, public_port):
        print(f'Deleting port mapping ({router_uuid}, {protocol}, {public_port})')

        router = UPnp._find_router(router_uuid)

        if not router:
            print(f'No router found with uuid {router_uuid}')

            return


        url = f'{router.base_url}{router.control_url}'

        print(f'Deleting port mapping ({public_port}/{protocol}) at {url}')

        headers = {
            'Host': f'{router.ip}:{router.port}',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPACTION': f'{router.type}#DeletePortMapping'
        }

        data = UPnp._delete_port_mapping_template.format(public_port, protocol)

        response = requests.post(url, data=data, headers=headers)

        print(response.text)

    @classmethod
    def list_port_mappings(cls, router_uuid):
        router = UPnp._find_router(router_uuid)

        if not router:
            print(f'No router found with uuid {router_uuid}')

            return


        url = f'{router.base_url}{router.control_url}'

        headers = {
            'Host': f'{router.ip}:{router.port}',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPACTION': f'{router.type}#GetGenericPortMappingEntry'
        }

        index = -1
        portmap_found = True
        portmaps = []

        while portmap_found:
            index += 1
            data = UPnp._list_port_mappings_template.format(index)
            response = requests.post(url, data=data, headers=headers)
            portmap = PortMapping.parse_port_map_xml(response.text, router.type)

            if portmap:
                portmaps.append(portmap)

            else:
                portmap_found = False   

        if portmaps:
            template = '{0:25}{1:30}{2:30}{3:10}{4:10}{5:20}'

            print(template.format('DESC', 'PUBLIC', 'PRIVATE', 'PROTOCOL', 'ENABLED', 'LEASE DURATION'))

            for portmap in portmaps:
                print(
                    template.format(
                        portmap.description,
                        f'{portmap.remote_host}:{portmap.public_port}',
                        f'{portmap.private_ip}:{portmap.private_port}',
                        portmap.protocol,
                        'Yes' if portmap.is_enabled else 'No',
                        portmap.lease_duration
                    )
                )
        else:
            print('No portmaps found')

    @classmethod
    def _find_router(cls, router_uuid):
        routers = SSDP.list()

        _default_router = None

        router = next((r for r in routers if r.uuid == router_uuid), _default_router)

        return router
