
import numpy as np
import pylab as plt
import time
import msvcrt
import getpass
from importlib import reload
from measurements.instruments import Lakeshore335 as LS335
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from tools import QPLemail

reload (LS335)
reload (QPLemail)

class Monitor ():

    def __init__ (self, bay = 2, temperature_ctrl = None):
        self._bay = bay
        self._name = 'bay'+str(bay)
        self._notifications = True
        self._wait_email = 300
        self._wait_T_readout = 1200
        self._offset = 100
        self._pwd = None

        if temperature_ctrl:
            self._Tctrl = temperature_ctrl
        else:
            self._Tctrl = None
            print ("No temperature controller!")

        self._max_T = 10

        self._scheduler = BlockingScheduler()
        self._scheduler.configure(timezone='UTC')
        self._scheduler.add_job(self._check_email, 'interval', seconds=10)
        self._scheduler.add_job(self._get_temperature, 'interval', seconds=3)

    def login (self):
        try:
           print ("Enter password...")
           self._pwd = getpass.getpass()
           self._email = QPLemail.QPLmail(bay=self._bay, password=self._pwd)
        except:
            print ("Login failed!")

    def set_max_temperature (self, T=10):
        self._max_T = T

    def _check_email (self):
        msg_dict = self._email.fetch_unread()

        for msg in msg_dict:
            body = msg['body'][0].as_string()
            print (msg)
            sender = msg['mail_from'][0]
            sender_addr = msg['mail_from'][1]
            print (sender)
            print (sender_addr)

            if (body.find ('notifications-off')>0):
                self._deactivate(sender)
            elif (body.find ('notifications-on')>0):
                self._activate(sender)
            elif (body.find('get-temperature')>0):
                T = self._get_temperature()
                # here I need to extract the sender email address, not the name
                self._email.send (to=[sender_addr], 
                            subject='Temperature readout', 
                            message='Current temperature: '+str(self.curr_T)+'K')
            elif (body.find ('send-report')>0):
                self._send_report()
            else:
                print ("None")

    def _send_alarm_email (self):
        self._email.send (to=['cb76@hw.ac.uk'], subject='Help!', 
                                message='Current temperature: '+str(self.curr_T)+'K')

    def _activate(self, sender):
        self._notifications = True
        print ("Notifications activated, as requested by: "+sender)
        self._email.send (to=['cb76@hw.ac.uk', sender_addr], subject='Settings change', 
                            message='Notifications activated, as requested by '+sender)

    def _deactivate(self, sender, sender_addr):
        self._notifications = False
        print ("Notifications de-activated, as requested by: "+sender)
        self._email.send (to=['cb76@hw.ac.uk', sender_addr], subject='Settings change', 
                            message='Notifications de-activated, as requested by '+sender)

    def _get_temperature (self, overrule_notifications=False):
        print ("Read temperature!")
        T = 5
        self._curr_T = T
        if (T>self._max_T):
            if (self._notifications):
                self._send_alarm_email()
        return self._curr_T

    def _send_report (self):
        pass

    def start (self):
        self._scheduler.start()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        try:
            while True:
                time.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            self._scheduler.shutdown()



