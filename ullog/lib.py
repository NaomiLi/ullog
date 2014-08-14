#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
# 
# Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
# 
# Included Libs:
#     SegmentTimedRotatingHanlder: inherited from logging.handlers.TimeRotatingHanlder. 
#         TimeRotatingHanlder split log after certain interval from u start program(logging)
#         but SegmentTimedRotatingHanlder need to split log at certain point--- not related to the start time
#     LevelFilter / NotLevelFilter: filter for logging different level log to different suffix log file
#     LogConfig: log config items for ullog
#
########################################################################
 
"""
File: lib.py
Author: Rui Li<lirui05@baidu.com>
Date: 2014/08/14 08:19:46
"""
import io
import os
import time
import datetime
import logging
import logging.handlers as _handler
import ConfigParser

class LevelFilter(object):
    def __init__(self, name='', level=logging.NOTSET):
        self.name = name
        self.level = level

    def filter(self, record):
        if isinstance(record, logging.LogRecord):
            if record.levelno == self.level:
                return 1
        return 0


class NotLevelFilter(object):
    def __init__(self, name='', level=logging.NOTSET):
        self.name = name
        self.level = level

    def filter(self, record):
        if isinstance(record, logging.LogRecord):
            if not record.levelno == self.level:
                return 1
        return 0


INTERVAL_UNIT = ['S', 'M', 'H', 'D']
class SegmentTimeRotatingFileHandler(_handler.TimedRotatingFileHandler):
    """
        Handlers for logging to a file, rotaing log file at certain time,
        but not related to the time when u start logging
        for instance:
            15minutes: it will rotate log file at :00, :15, :30, :45 in one hour
            1day:      it will rotate log file at midnight 0:00
        Compared with TimedRotatingFileHandler, it rotate log file at certain
        timed interval, the start time is when u start logging
        To be simple, this class just support the following interval unit:
            [second, minute, hour, day]
    """
    def __init__(self, filename, suffix, when='h', interval=1, backupCount=0, 
            encoding=None, delay=False, utc=False):
        """Args:
                    when: interval unit
                filename: log file's prefix
                  suffix: log file's suffix
        """
        # check when 
        if when.upper() not in INTERVAL_UNIT:
            raise TypeError("Invalid rollover interval specified: %s" % self.when)
        self.interval_num = interval
        super(SegmentTimeRotatingFileHandler, self).__init__(
            filename, when, interval, backupCount, encoding, delay, utc)
        self.suffix += '.%s' % (suffix)
        self.prefix=filename

        # to create the first timed file
 #       self.rolloverAt -= self.interval
        self.doRollover() 
        # remove the default file named by self.prefix
        if os.path.isfile(self.prefix):
            os.remove(self.prefix)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        t = self.rolloverAt
        timeTuple = self.int2time(t)
        dfn = self.prefix + "." + time.strftime(self.suffix, timeTuple)
        self.baseFilename = dfn
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        self.mode = 'a'
        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        self.rolloverAt = newRolloverAt

    def computeRollover(self, currentTime):
        """
            Calculate the rollover time based on the specified time.
        """
        currentTime = self.parseCurrentTime(currentTime)
        result = currentTime + self.interval
        return result

    def parseCurrentTime(self, currentTime):
        t = self.int2time(currentTime)
        if self.when == 'H':
            format = '%Y-%m-%d:%H'
            result = time.mktime(time.strptime(time.strftime(format, t), format))
        elif self.when == 'D':
            format = '%Y-%m-%d'
            result = time.mktime(time.strptime(time.strftime(format, t), format))
        elif self.when == 'S':
            format = '%Y-%m-%d:%H:%M'
            result = time.mktime(time.strptime(time.strftime(format, t), format))
        elif self.when == 'M':
            # if current time is "14:07" and rollover is 15minutes,
            # log should be written in file named "***.14_15.**"
            format = '%Y-%m-%d %H:%M'
            currentTime = time.mktime(time.strptime(time.strftime(format, t), format))
            minute = int(t[4]) 
            interval_unit = self.interval / self.interval_num
            while minute % self.interval_num != 0: # to find the rollover point
                currentTime -= interval_unit
                minute = int(self.int2time(currentTime)[4])
            result = currentTime
        else:
            raise TypeError('param "when" is only allowed in [S, M, H, D]')
        return result

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.
                                                                            
        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.prefix)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def int2time(self, time_int):
        if self.utc:
            t = time.gmtime(time_int)
        else:
            t = time.localtime(time_int)
        return t


class LogConfig(object):

    def __init__(self, config_parser=None):
        self._level = None
        self._formatter = None
        self._directory = None
        self._prefix = None
        self._is_split = None
        self._interval =  None
        self._interval_unit = None
        self._level_pairs = []
        self.config = config_parser
        if self.config is not None:
            self.parse()

    def parse(self):
        if self.config is None:
            return
        self._directory = self._get_item('LOG', 'directory')
        self._prefix = self._get_item('LOG', 'prefix')
        self._is_split = self._get_item('LOG', 'is_split')
        self._interval = self._get_item('LOG', 'interval')
        self._interval_unit = self._get_item('LOG', 'interval_unit')
        # parse level pairs
        for section in self.config.sections():
            if 'LEVEL' in section:
                try:
                    # level=DEBUG,INFO
                    # suffix=nt.log
                    level = self.config.get(section, 'level').split(',')
                    suffix = self.config.get(section, 'suffix')
                    self._level_pairs.append((level, suffix))
                except (ConfigParser.Error, KeyError) as e:
                    continue

    def _get_item(self, section, option):
        try:
            value = self.config.get(section, option)
            return value
        except (TypeError, ValueError, ConfigParser.Error) as e:
            pass

    @property
    def level(self):
        if self._level is None:
            self._level = logging.DEBUG
        return self._level

    @level.setter
    def level(self, level):
        try:
            level = int(level)
        except TypeError:
            raise TypeError('level must be integer, level=[%s]' % (str(level)))
        self._level = level

    @property
    def formatter(self):
        if self._formatter is None:
            self._formatter = logging.Formatter(
                '[%(asctime)s][%(levelname)s][%(filename)s:%(funcName)s:%(lineno)d]: %(message)s')
        return self._formatter

    @formatter.setter
    def formatter(self, formatter):
        if isinstance(formatter, logging.Formatter):
            self._formatter = formatter
        if isinstance(formatter, basestring):
            self._formatter = logging.Formatter(formatter)
            
    @property
    def directory(self):
        if self._directory is None:
            self._directory = os.path.abspath('.')
        if not os.path.isdir(self._directory):
            os.makedirs(self._directory)                
        return self._directory

    @directory.setter
    def directory(self, directory):
        self._directory = directory

    @property
    def prefix(self):
        if self._prefix is None:
            self._prefix = datetime.datetime.today().strftime('%Y-%m-%d')
        return self._prefix

    @prefix.setter
    def prefix(self, prefix):
        self._prefix = prefix

    @property
    def is_split(self):
        if self._is_split is None:
            self._is_split = 0
        return bool(self._is_split)

    @is_split.setter
    def is_split(self, is_split):
        try:
            is_split = int(is_split)
        except TypeError:
            raise TypeError('is_split must be integer, is_split=[%s]' % (str(is_split)))
        self._is_split = is_split

    @property
    def interval(self):
        if self._interval is None:
            self._interval = 1
        return self._interval

    @interval.setter
    def interval(self, interval):
        try:
            interval = int(interval)
        except TypeError:
            raise TypeError('interval must be integer, interval=[%s]' % (str(interval)))
        self._interval = interval

    @property
    def interval_unit(self):
        if self._interval_unit is None:
            self._interval_unit = 'D'
        return self._interval_unit

    @interval_unit.setter
    def interval_unit(self, interval_unit):
        if interval_unit.upper() not in INTERVAL_UNIT:
            raise TypeError('interval_unit must be in %s' % (str(INTERVAL_UNIT)))
        self._interval_unit = interval_unit
    
    @property
    def level_pairs(self):
        return self._level_pairs

if __name__ == "__main__":
    pass
