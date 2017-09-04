from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
from nanpy import ArduinoApi, SerialManager
from time import sleep
from threading import Thread
import time
import datetime
import os, sys, traceback

log = logging.getLogger('Light')


class Light():
    def __init__(self,lid,board_pin_id,garage_key, usbConnectHandler):
        self.config_handler = ConfigManager()
        self.light_id=lid
        self.light_gname = garage_key
        self.l_name=garage_key+"_" + lid
        self.board_pin_id = board_pin_id
        self.l_update_time = time.time()
        self.usbConnectHandler = usbConnectHandler
        self.status="OFF"
        strlog = "%s created (board pin %d)" % (self.l_name,board_pin_id)
        log.info(strlog)
        self.thread_light_flash = None
        self.relayLOWEnableList=(self.config_handler.getConfigParam('GARAGE_COMMON', "GarageRelayLOWEnable")).split(',')
        self.stop_thread = False
        pass

    def commandLight(self,cmd):
        high=self.usbConnectHandler.HIGH
        low=self.usbConnectHandler.LOW

        #Handle those relays that are reversed
        if (str(self.board_pin_id) in self.relayLOWEnableList):
            high = self.usbConnectHandler.LOW
            low = self.usbConnectHandler.HIGH

        if (self.usbConnectHandler != None):
            self.l_update_time = time.time()
            if (cmd == "ON"):
                self.usbConnectHandler.digitalWrite(self.board_pin_id, high)
            else:
                self.usbConnectHandler.digitalWrite(self.board_pin_id, low)

            strlog = "%s %s Turn %s" % (self.light_gname, self.light_id,cmd)
            log.debug(strlog)
        pass


    def turnOffLight(self):
        self.status = "OFF"
        self.commandLight(self.status)

    def turnOnLight(self):
        self.status = "ON"
        self.commandLight(self.status)

    def startFlashLight(self):
        strlog = "%s %s Start Flashing" % (self.light_gname, self.light_id)
        log.debug(strlog)
        self.stop_thread = False
        # light_manager=Light()
        if (self.thread_light_flash == None):
            self.thread_light_flash = Thread(target=self.flashLight,name=self.l_name,daemon=False)
        try:
            strlog = "%s %s Start Flashing thread start" % (self.light_gname, self.light_id)
            log.info(strlog)
            self.thread_light_flash.start()
        except Exception:
            strlog = "%s %s Start Flashing thread Eception.  Already started ?" % (self.light_gname, self.light_id)
            log.info(strlog)

    def stopFlashLight(self):
        strlog = "%s %s Stop Flashing" % (self.light_gname, self.light_id)
        log.info(strlog)
        self.stop_thread = True
        if (self.thread_light_flash == None):
            return
        try:
            self.stop_thread = True
            self.thread_light_flash == None
            self.thread_light_flash.join()
            strlog = "%s %s Stop Flashing AFTER thread join" % (self.light_gname, self.light_id)
            log.info(strlog)
        except Exception:
            self.thread_light_flash = None
            strlog = "%s %s Stop Flashing Exception" % (self.light_gname, self.light_id)
            traceback.print_exc()

    def monitor(self):

        pass


    def flashLight(self):
        crazyloop=0;
        while (self.stop_thread == False
               and crazyloop<90): #2 sec loop

            strlog = "%s %s flashing Light !" % (self.light_gname, self.light_id)
            log.debug(strlog)
            crazyloop+=1
            if self.stop_thread == False: #Skip flash on thread stop
                sleep(1.000)
                if (self.status == "OFF" and self.stop_thread == False):
                    self.commandLight("ON")
                else:
                    self.commandLight("OFF")
                sleep(1.000)
            self.commandLight(self.status)

    def connectUSB(self,usbConnectHandler):
        strlog = "%s %s Re-connect USB (board pin %d) !" % (self.light_gname, self.light_id, self.board_pin_id)
        log.info(strlog)
        self.usbConnectHandler = usbConnectHandler

        self.thread_light_flash.stop()

        self.thread_light_flash = Thread(target=Light.flashLight,
                                         args=(self,), name=self.l_name,
                                         daemon=True)

        # self.initBoardPinModeOutput(self.board_pin_id)

