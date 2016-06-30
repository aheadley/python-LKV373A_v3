#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import functools
import urlparse

import requests


def v3_api_request(*pargs, **kwargs):
    def outer_func(func):
        action = func.__name__

        @functools.wraps(func)
        def inner_func(self, *inner_pargs, **inner_kwargs):
            response = requests.get(self.url)

            result = func(self, response)

        return inner_func

    return outer_func

def require_reboot(func):
    @functools.wraps(func)
    def inner_func(self, *pargs, **kwargs):
        result = func(self, *pargs, **kwargs)
        self.reboot()
        return result

    return inner_func

def parse_url_params(url):
    params = urlparse.parse_qs(urlparse.urlparse(url).query)
    for k, v in params.iteritems():
        params[k] = v[0]
    return params

class LKV373A_v3(object):
    DEFAULT_IP_ADDR         = '192.168.1.238'
    ENDPOINT_URL_TPL        = 'http://{ip_addr}/dev/info.cgi'

    def __init__(self, ip_addr=DEFAULT_IP_ADDR):
        self._ip_addr = ip_addr

    @property
    def url(self):
        return self.ENDPOINT_URL_TPL.format(ip_addr=self._ip_addr)

    @v3_api_request(reboot='Reboot')
    def reboot(self, response):
        return response.ok

    @v3_api_request(Reset='Reset')
    def Reset(self, response):
        return response.ok

    @v3_api_request('selaudio_type', 'selaudio_sprate', 'selaudio_brate')
    def audioinfo(self, response):
        return response.ok

    @v3_api_request('hdmi', 'cvbs', 'videoin_res', 'videoin_frate', 'videoout_fhd', \
        'videoout_hd', 'videoout_brate_fhd', 'videoout_brate_hd', 'videoout_brate_sd')
    def videoinfo(self, response):
        return response.ok

    @v3_api_request('udp', 'rtp', 'multicast', 'unicast', 'mcastaddr', 'port')
    def streaminfo(self, response):
        return response.ok

    @v3_api_request('ip_addr', 'netmask', 'gateway')
    def network(self, response):
        if response.ok:
            original_params = parse_url_params(response.request.url)
            new_ip = '.'.join(original_params['ipaddr%d' % i] for i in range(4))
            self._ip_addr = new_ip
        return response.ok

    @network.modify_params
    def network_modify_params(self, params):
        new_params = {}
        new_params.update({'ipaddr%d' % i: e, \
            for i, e in enumerate(params['ip_addr'].split('.'))})
        new_params.update({'netmask%d' % i: e, \
            for i, e in enumerate(params['netmask'].split('.'))})
        new_params.update({'gw%d' % i: e, \
            for i, e in enumerate(params['gateway'].split('.'))})
        return new_params

    @v3_api_request('mac_addr')
    def macaddr(self, response):
        return response.ok

    @macaddr.modify_params
    def macaddr_modify_params(self, params):
        new_params = {'macaddr%d' % i: e, \
            for i, e in enumerate(params['mac_addr'].split(':'))}
        return new_params


if __name__ == '__main__':
    import optparse

    pass
