from ..lib import SBComponent

class nfc(SBComponent.SBComponent_MQTT_SB):

    opts_req = {    # dict required options
        'platform':     ('PN532',),  # dictionary of platform specific options - currently we only support GPIOs as inputs
        'instance':     str,
        'platform_indicator': ('led',),
        'indicator_instance': str,
    }

    deps = opts_req['platform']  # list of platform dependencies



    def init(self):
        # lookup platform instance
        self.pn532 = SBComponent.component_instances[self.opts['platform']][self.opts['instance']]
        self.indicator = SBComponent.component_instances[self.opts['platform_indicator']][self.opts['indicator_instance']]
        self.pn532.add_cb(self.on_nfc_detect)

        self.settings['aid'] = "A0000008340001"  # Setting AID to Sensorberg AID to have a default AID without setting the settings via MQTT
        self.pn532.set_aid(self.settings['aid'])

    def callback(self, payload, args, res):
        self.log.debug("Callback received: '{}' on '{}'".format(payload, args))
        if args[0] == 'reset':
            self.pn532.reset()

    def on_nfc_detect(self, pl):
        self.publish(pl)
        self.indicator.show_feedback()

    def on_settings_updated(self):
        if 'aid' in self.settings:
            self.pn532.set_aid(self.settings['aid'])
