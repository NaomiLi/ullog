ullog
=====
     Module: Ullog
 
      Two Features:
          1. U can configure different(by suffix) output log file for different level when logging
            for instance: **.wf.log for WARNING and FATAL  while **.nt.log for NOTICE and DEBUG
           2. Split log at certain interval time
              Related configs are: interval_unit(eg, "M" minute) and interval(eg, "1")
              This means that log file will be splitted at **:00, **:15, **:30, **:45, 
              four splitter logs in one hour and of course, these files' name are tagged with time below
              2014-08-14_19_00.log / 2014-08-14_19_15.log / 2014-08-14_19_30.log/ 2014-08-14_19_45.log
     
     How to Install
          python setup.py build
          python setup.py install

     How to Use:
           import ullog
           ul_log = ullog.Ullog.getInstance('test_name')
           logger = ul_log.getLogger()   
           logger.warning('warning-test')

           Also, before start to logging, u can configure items below:
           1.by configparser
            [LOG]
            level=WARNING           # lowest log level
            formatter=[%(asctime)s][%(levelname)s]: %(message)s
            directory=log           # directory of all logs
            prefix=test             # prefix's of log file, eg: test.2014-08-14_19.log
            is_split=1              # whether log will be splitted in certain time. 1:split, 0:not split
            interval=1                
            interval_unit=H #hour   # options: [S, M, H, D] (means second, minute, hour, day)
            [WF_LEVEL]              # LEVEL config item must make "LEVEL" included
            level=WARNING,FATAL     # options: [DEBUG, INFO, WARNING, FATAL, ERROR]
            suffix=wf.log           # output log file's suffix
            [NT_LEVEL]
            level=INFO
            suffix=nt.log
           2.by ullog methods: basicConfig, addLevelHandler
           ul_log.basicConfig(level=ullog.INFO, 
                              directory='.', 
                              prefix="haha", 
                              is_split=1,
                              interval_unit='H',
                              interval=1)
           ul_log.addLevelHandler(level=ullog.WARNING, suffix="wf.log")
