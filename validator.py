#!/usr/bin/env python
# coding:utf-8
from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool
from logger import logger
import re
import time
import pyip
import requests
from config import VALIDATE_CONFIG


class Validator:
    def __init__(self):
        self.target = VALIDATE_CONFIG['TARGET']
        self.timeout = VALIDATE_CONFIG['TIMEOUT']
        self.thread_num = VALIDATE_CONFIG['THREAD_NUM']
        self.pattern = re.compile(
            r'((?:IP:Port)|(?:HTTP_CLIENT_IP)|(?:HTTP_X_FORWARDED_FOR))</td>\n?\s*<td.*?>(.*?)</td>', re.I)
        self.ip = self._get_self_ip()
        self.IPL = pyip.IPLocator('QQWry.Dat')

    def run(self, proxies):
        # 采用gevent进行处理
    #    if not self.ip:
    #        logger.error('Validating fail, self ip is empty')
    #        return []
        pool = Pool(self.thread_num)
        avaliable_proxies = filter(lambda x: x, pool.map(self.validate, proxies))
        logger.info('Get %s avaliable proxies' % len(avaliable_proxies))
        return avaliable_proxies

    def validate(self, proxy):
        try:
            start = time.time()
            r = requests.get(self.target, proxies={'http': 'http://%s' % proxy}, timeout=self.timeout)
            if r.ok and r.content.strip() != self.ip:
                speed = time.time() - start
                logger.info('Validating %s, success, type:%s, time:%ss', proxy, 0, speed)
                return {
                    'ip': proxy.split(':')[0],
                    'port': proxy.split(':')[1],
                    'type': 0,
                    'speed': speed,
                    'area': self.IPL.getIpAddr(self.IPL.str2ip(proxy.split(':')[0]))
                }
        except Exception as e:
            logger.debug('Validating %s, fail: %s', proxy, e)
            pass
        return None

    def _get_self_ip(self):
        # 获取自身外网ip
        try:
            r = requests.get(self.target, timeout=5)
            if r.ok:
                ip = r.content.strip()
                logger.info('Get self ip success: %s' % ip)
                return ip
        except Exception, e:
            logger.warn('Get self ip fail, %s' % e)
            return ''
