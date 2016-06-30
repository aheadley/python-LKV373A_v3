#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import functools
import urlparse

import requests


def v3_api_request(*pargs, **kwargs):
    def outer_func(orig_func):
        action = orig_func.__name__

        @functools.wraps(orig_func)
        def inner_func(self, *args, **opts):
            params = dict(zip(pargs, args))
            params.update(opts)
            try:
                params = getattr(self, action).prepare_params(params)
            except AttributeError:
                pass
            params['action'] = action
            params.update(kwargs)

            response = requests.get(self.url, params=params)
            return orig_func(self, response)

        def param_prepper(mfunc):
            inner_func.prepare_params = mfunc

        inner_func.param_prepper = param_prepper
        return inner_func

    return outer_func

# def require_reboot(func):
#     @functools.wraps(func)
#     def inner_func(self, *pargs, **kwargs):
#         result = func(self, *pargs, **kwargs)
#         self.reboot()
#         return result

#     return inner_func

def parse_url_params(url):
    params = urlparse.parse_qs(urlparse.urlparse(url).query)
    for k, v in params.iteritems():
        params[k] = v[0]
    return params

class LKV373A_v3(object):
    DEFAULTS = {
        'DEVICE_IP_ADDRESS':    '192.168.1.238',
        'DEVICE_PORT':          80,
        'BROADCAST_ADDRESS':    '239.255.43.43',
        'BROADCAST_PORT':       5004,
    }

    # ENDPOINT_URL_TPL        = 'http://{ip_addr}:{port}/dev/info.cgi'
    ENDPOINT_URL_TPL        = 'http://requestb.in/1d8hd971'

    def __init__(self, ip_addr=DEFAULTS['DEVICE_IP_ADDRESS'], port=DEFAULTS['DEVICE_PORT']):
        self._ip_addr = ip_addr
        self._port = port

    @property
    def url(self):
        return self.ENDPOINT_URL_TPL.format(ip_addr=self._ip_addr, port=self._port)

    @v3_api_request(reboot='Reboot')
    def reboot(self, response):
        return response.ok

    @v3_api_request(Reset='Reset')
    def Reset(self, response):
        return response.ok

    @v3_api_request('selaudio_type', 'selaudio_sprate', 'selaudio_brate')
    def audioinfo(self, response):
        return response.ok

    @v3_api_request('videoin_res', 'videoin_frate', 'videoout_fhd', \
        'videoout_hd', 'videoout_brate_fhd', 'videoout_brate_hd', 'videoout_brate_sd', \
        hdmi='y', cvbs='n')
    def videoinfo(self, response):
        return response.ok

    @v3_api_request('udp', 'rtp', 'multicast', 'unicast', 'mcastaddr', 'port')
    def streaminfo(self, response):
        return response.ok

    @v3_api_request('ipaddr', 'netmask', 'gw', 'dhcp')
    def network(self, response):
        if response.ok:
            original_params = parse_url_params(response.request.url)
            new_ip = '.'.join(original_params['ipaddr%d' % i] for i in range(4))
            self._ip_addr = new_ip
        return response.ok

    @network.param_prepper
    def network_prepare_params(params):
        print 'fix network'
        new_params = {}
        keys = params.keys()
        if 'dhcp' in keys:
            new_params['dhcp'] = params['dhcp']
            del params['dhcp']
        for k in keys:
            new_params.update({k + str(i): v for i, v in enumerate(params[k].split('.'))})

        return new_params

    @v3_api_request('macaddr')
    def macaddr(self, response):
        return response.ok

    @macaddr.param_prepper
    def macaddr_prepare_params(self, params):
        new_params = {'macaddr%d' % i: v \
            for i, v in enumerate(params['macaddr'].split(':'))}
        return new_params

    @v3_api_request('ssid', 'password', 'security')
    def softap(self, response):
        return response.ok

    @v3_api_request('ssid', 'password', 'security')
    def wifi(self, response):
        return response.ok

if __name__ == '__main__':
    import sys
    import optparse

    parser = optparse.OptionParser()

    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.print_usage()
        sys.exit(1)

    dev_ip_addr = args[0]

    obj = LKV373A_v3(dev_ip_addr)
