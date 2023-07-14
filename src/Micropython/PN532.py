import uasyncio as asyncio
import time
from machine import Pin
import json
import ubinascii
from adafruit_pn532 import spi as nfc_spi
from ..lib import SBComponent

SELECT_OK = bytearray([0x00, 0x90, 0x00])
COMMAND_ERROR = bytearray([0x00, 0x6f, 0x00])
GET_UUID_COMMAND = [0x01, 0x03, 0x03, 0x07]

_PHONE   = "phone"
_CARD    = "card"

_SEC_IGNORE_TAG = const(5)

class PN532(SBComponent.SBComponent_MQTT_SB):  # inheriting from _MQTT

    opts_req = {  # dict required options
        'platform': ('SPI',),  # tuple of expected values
        'platform_instance': str,  # expects object of class 'str'
        'platform_options': dict,  # dictionary of platform specific options
    }
    opts_opt = {  # dict of optional options
        'irq': int,
        'reset': int,
    }

    deps = opts_req['platform']  # list of platform dependencies

    def init(self):
        # lookup platform instance
        spi_bus = SBComponent.component_instances[self.opts['platform']][self.opts['platform_instance']].spi
        irq = self.opts['irq']
        rst = self.opts['reset']
        self.aid = []

        if self.opts['platform'] == 'SPI':
            spi_cs = Pin(self.opts['platform_options']['cs_pin'], Pin.OUT)

        self.rst_pin = Pin(rst, Pin.OUT)
        self.rst_pin.on()

        self.irq_pin = Pin(irq, Pin.IN) # we rely on the peripheral driving its state, so no pull-up/-down - besides, pin is probably 35, which on esp32 (wrover) doesn't have an internal pull-up/-down anyway

        self.last_triggered = 0
        self.last_seen = (b"", 0) # currently unused
        self.ignore_next_int = True # skip the first upcoming interrupt (triggered by activation of listening mode below)

        self.lock = asyncio.Lock()

        self.pn532 = nfc_spi.PN532_SPI(spi_bus, spi_cs)
        self.pn532.set_receiver_gain()
        self.pn532.SAM_configuration()
        self.enable_irq()
        self.pn532.listen_for_passive_target() # raises an interrupt which will be skipped due to self.ignore_next_int=True

    def set_aid(self, aid):
        # set aid as integer list
        self.aid = list(ubinascii.unhexlify(aid))

    def reset(self):
        # There is a method in the PN532 implementation of adafruit but it crashes when setting the pin value, so I implemented it
        self.log.debug("Reset PN532 IC")
        self.ignore_next_int = True
        self.disable_irq()  # had to remove the interrupt otherwise the re-init does not work properly

        self.rst_pin.off()
        time.sleep(0.5)
        self.rst_pin.on()
        time.sleep(0.1)

        self.init()

    def enable_irq(self):
        self.log.debug("Enabling interrupt handler for IRQ pin")
        self.irq_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._on_nfc_int)

    def disable_irq(self):
        self.log.debug("Disabling interrupt handler for IRQ pin")
        self.irq_pin.irq(trigger=Pin.IRQ_FALLING, handler=None)

    def _publish_detected(self, pl): # at the point of this func being called the pin state might already have changed, so we dismiss the passed instance entirely, as of no use to us
        #self.publish(pl)
        self.call_cbs(pl)

    def _on_nfc_int(self, pin=None):

        def __exit():
            self.ignore_next_int = True
            self.enable_irq()
            self.pn532.listen_for_passive_target()

        self.log.debug("Interrupt triggered on pin {}.".format(pin))
        if self.lock.locked(): # due to implementation details soft interrupts are queued up and will only be executed non-concurrent, one after another - so this case will never happen, but let's not rely on implementation details here..
            self.log.error("NFC currently already processing - skipping.")
            return
        if self.ignore_next_int:
            self.log.debug("Interrupt declared to be skipped - next will trigger processing again.")
            self.ignore_next_int = False
            return
        #if (self.last_triggered + _SEC_IGNORE_TAG) >= time.time():
        #    self.log.warning("Debouncing -> skipping interrupt.")
        #    return __exit()

        self.log.debug("NFC tag detected.".format(pin))
        self.last_triggered = time.time()

        #TODO: Interrupts might queue up here long after the initial one is already processed. We will need to skip them based on timestamps.

        # `schedule()` called implicitly as part of the esp32 port (mod_machine.c)
        self.disable_irq() # NFC transfers cause interrupts which we want to ignore as much and as soon as possible, as they might queue up and causing read attempts once the actual processing is long finished already. By disabling interrupts while processing we try to get away without properly tracking timestamps and skipping/debouncing based on them

        # exception handling is messy with asyncio, we have to rely on if _on_detected() throws an exception, that the component gets reinitialised by the main loop exception handler
        asyncio.create_task(self._on_detected(__exit))

    async def _on_detected(self, finished_cb):
        async with self.lock: # while schedule() queues interrupts and handles them sequentially in reality, let's not reply on this implementation detail
            try:
                res = b""
                retries = 0
                while not res and retries <= 3:
                    self.log.debug("Tag read attempt: {}".format(retries+1))
                    res = self.pn532.get_passive_target(timeout=0.5)
                    retries += 1
                if res:
                    self.log.debug("Raw response: {}".format(res))
                    uid = res[6 : 6 + res[5]]
                    self.log.debug("Parsed UUID: {}".format(uid))
                    uid = "".join("{:02x}".format(i) for i in uid)
                    apdu_avail = self.pn532.check_if_apdu_avail(res[2:5])
                    self.log.debug("NFC tag APDU capable? {}".format(apdu_avail))
                    if apdu_avail:
                        self.select_apdu(uid)
                    else:
                        pass
                        self._publish_detected(self.create_req({'nfc_device_type': _CARD, 'nfc_device_identifier': uid}))
                    self.last_seen = (res, time.time())
                else:
                    self.log.error("No response from tag after {} attempts -> giving up".format(retries))
#                if res == self.last_seen[0] and (self.last_seen[1] + _SEC_IGNORE_TAG) > time.time():
#                    self.log.debug("Debouncing for {} seconds and ignoring tag for {} seconds.".format(2, _SEC_IGNORE_TAG))
#                    await asyncio.sleep(_SEC_IGNORE_TAG)
#                    return
                await asyncio.sleep(_SEC_IGNORE_TAG)
            except:
                await asyncio.sleep(_SEC_IGNORE_TAG/10)
        finished_cb()

    def select_apdu(self, uid):
        try:
            resp = self.select_apdu_retry()
            if resp:
                if resp == SELECT_OK:  # success
                    self.log.debug("APDU select succeeded.")
                    payload = self.send_data_retry()
                    if payload:
                        self.log.debug("APDU raw payload received: {}".format(payload))
                        readable_payload = payload.decode("utf-8")[1:]
                        self.log.debug("APDU parsed payload: {0}".format(readable_payload))
                        self._publish_detected(self.create_req({'nfc_device_type': _PHONE, 'nfc_device_identifier': uid, 'nfc_payload': readable_payload}))
                    else:
                        self.log.error("No data received via APDU.")
            else:
                self.log.error("No response for APDU select.")
        except Exception as exc:
            self.log.exc(exc, "Selecting APDU failed")
            raise exc

    def select_apdu_retry(self):
        if not self.aid:
            raise RuntimeError("Selecting APDU failed - no AID available")

        resp = None
        retry = 0
        while not resp:
            retry += 1
            resp = self.pn532.select_apdu(self.aid)
            if resp is not None and len(resp) <= 2:
                resp = None
            if retry >= 5:
                raise RuntimeError("Selecting APDU failed")
        return resp

    def send_data_retry(self):
        resp = None
        retry = 0
        while resp is None:
            retry += 1
            resp = self.pn532.send_data(GET_UUID_COMMAND, 128)
            if resp is not None and len(resp) <= 2:  # if payload was just one byte long for no reason wtF?
                resp = None
            if resp == COMMAND_ERROR:
                raise RuntimeError("Command error received from device")
            if retry >= 2:
                raise RuntimeError("Sending data failed")
        return resp
