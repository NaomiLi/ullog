#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
# 
# Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved

# Author: Rui Li<lirui05@baidu.com>
# Date: 2014/08/11 10:34:28
#
# Module: Ullog
# 
# Two Features:
#    1. U can configure different(by suffix) output log file for different level when logging
#       for instance: **.wf.log for WARNING and FATAL  while **.nt.log for NOTICE and DEBUG
#    2. Split log at certain interval time
#       Related configs are: interval_unit(eg, "M" minute) and interval(eg, "1")
#       This means that log file will be splitted at **:00, **:15, **:30, **:45, 
#       four splitter logs in one hour and of course, these files' name are tagged with time below
#       2014-08-14_19_00.log / 2014-08-14_19_15.log / 2014-08-14_19_30.log/ 2014-08-14_19_45.log
#
# How to Use:
#   import ullog
#   ul_log = ullog.Ullog.getInstance('test_name')
#   logger = ul_log.getLogger()   
#   logger.warning('warning-test')
#
#   Also, before start to logging, u can configure items below:
#   1.by configparser
#   [LOG]
#   level=WARNING           # lowest log level
#   formatter=[%(asctime)s][%(levelname)s]: %(message)s
#   directory=log           # directory of all logs
#   prefix=test             # prefix's of log file, eg: test.2014-08-14_19.log
#   is_split=1              # whether log will be splitted in certain time. 1:split, 0:not split
#   interval=1                
#   interval_unit=H #hour   # options: [S, M, H, D] (means second, minute, hour, day)
#   [WF_LEVEL]              # LEVEL config item must make "LEVEL" included
#   level=WARNING,FATAL     # level filter
#   suffix=wf.log           # output log file's suffix
#   [NT_LEVEL]
#   level=INFO
#   suffix=nt.log
#   2.by ullog methods: basicConfig, addLevelHandler
#    
########################################################################
 
import io
import os
import ConfigParser
import threading
import logging
import logging.handlers as _handler
import lib as _lib


DEBUG     = logging.DEBUG
INFO      = logging.INFO
WARNING   = logging.WARNING
CRITICAL  = logging.CRITICAL
ERROR     = logging.ERROR
FATAL     = logging.FATAL

LEVELS = {'DEBUG':    DEBUG,
          'INFO':     INFO,
          'WARNING':  WARNING,
          'CRITICAL': CRITICAL,
          'ERROR':    ERROR,
          'FATAL':    FATAL}

INTERVAL_UNIT = ['S', 'M', 'H', 'D']

_locker = threading.RLock()
class Ullog(object):
    instances = []

    @staticmethod
    def getInstance(name):
        idx = -1
        for i in range(len(Ullog.instances)):
            if Ullog.instances[i].name == name:
                idx = i
                break
        if idx == -1:
            _locker.acquire()
            instance = Ullog(name=name)
            Ullog.instances.append(instance)
            _locker.release()
        else:
            instance = Ullog.instances[idx]
        return instance

    def getLogger(self):
        return self.logger

    def __init__(self, name):
        self.name = name
        self.log_config = _lib.LogConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self._setDefaultHanlder()

    def _setDefaultHanlder(self):
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
            if os.path.isfile(handler.baseFilename):
                os.remove(handler.baseFilename)
        self.default_handler = self._getFileHandler(suffix='log')
        self.logger.addHandler(self.default_handler)

    def _getFileHandler(self, suffix='log'):
        log_path = os.path.join(self.log_config.directory, self.log_config.prefix)
        if self.log_config.is_split == 0:
            log_path = '%s.%s' % (log_path, suffix)
            file_handler = logging.FileHandler(log_path)
        else:
            file_handler = _lib.CertainSegmentsTimeRotatingFileHandler(filename=log_path,
                                                          suffix=suffix,
                                                          when=self.log_config.interval_unit,
                                                          interval=self.log_config.interval)
        file_handler.setFormatter(self.log_config.formatter)
        return file_handler
        
    def setLevel(self, level):
        self.logger.setLevel(level)    

    def basicConfig(self, level=None, formatter=None, directory=None, prefix=None, is_split=None,
            interval=None, interval_unit=None):
        self.log_config.level = level
        self.log_config.formatter = formatter
        self.log_config.directory = directory
        self.log_config.prefix = prefix
        self.log_config.is_split = is_split
        self.log_config.interval = interval
        self.log_config.interval_unit = interval_unit
        #set level and file handler
        self.setLevel(level)
        self._setDefaultHanlder()

    def addLevelHandler(self, level, suffix):
        if not (isinstance(level, int) and isinstance(suffix, basestring)):
            raise TypeError("level must be interge and suffix must be string or unicode")
        if isinstance(suffix, unicode):
            suffix = suffix.encode('utf-8')
        file_handler = self._getFileHandler(suffix=suffix)
        level_filter = _lib.LevelFilter(level=level)
        file_handler.addFilter(level_filter)
        self.logger.addHandler(file_handler)

        #remove "level" from default_handler
        not_level_filter = _lib.NotLevelFilter(level=level)
        self.default_handler.addFilter(not_level_filter)

    def loadConf(self, config_parser=None):
        if isinstance(config_parser, ConfigParser.RawConfigParser):
            self.log_config = _lib.LogConfig(config_parser=config_parser)
        self.basicConfig(level=self.log_config.level,
                         formatter=self.log_config.formatter,
                         directory=self.log_config.directory,
                         prefix=self.log_config.prefix,
                         is_split=self.log_config.is_split,
                         interval=self.log_config.interval,
                         interval_unit=self.log_config.interval_unit)
        for level_list, suffix in self.log_config.level_pairs:
            for level in level_list:
                level = LEVELS[level]
                self.addLevelHandler(level, suffix)

if __name__ == "__main__":
############################# Test Part #####################
    TEST1_LOG_CONFIG="""
    [LOG]
    directory=log
    prefix=test
    is_split=1
    interval_unit=D
    interval=1
    [WF_LEVEL]
    level=WARNING
    suffix=wf.log
    """
    # init
    s_ullog = Ullog.getInstance('test')
    # config
    # 1. config by basicConfig and then addLevelHandler
    #s_ullog.basicConfig(level=INFO, 
    #                    directory='.', 
    #                    prefix="haha", 
    #                    is_split=1,
    #                    interval_unit='H',
    #                    interval=1)
    #s_ullog.addLevelHandler(level=WARNING, suffix="wf.log")
    # 2. config by loading ConfigParser.RawConfiParser instance
    #import io
    #import ConfigParser
    #config_parser = ConfigParser.RawConfigParser()
    #config_parser.readfp(io.BytesIO(TEST1_LOG_CONFIG.replace(' ', '')))
    #s_ullog.loadConf(config_parser)
    
    logger = s_ullog.getLogger()
    logger.warning('213')
    logger.info('info')
