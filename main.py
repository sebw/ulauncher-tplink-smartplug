import json
import socket
import logging
import datetime
from time import sleep
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

logger = logging.getLogger(__name__)

class DemoExtension(Extension):

    def __init__(self):
        super(DemoExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        logger.info('preferences %s' % json.dumps(extension.preferences))

        # Fetching plug IP from prefs
        plug_name = extension.preferences['plug_ip']
        if plug_name != "":
            plug_name_list = plug_name.split(' ')
        else:
            plug_name_list = None

        # Fetch light bulb IP from prefs
        bulb_name = extension.preferences['bulb_ip']
        if bulb_name != "":
            bulb_name_list = bulb_name.split(' ')
        else:
            bulb_name_list = None

        try:
            import pyHS100 as p
        except:
            logger.info('Python library pyHS100 missing.')
            items.append(ExtensionResultItem(icon='images/icon_unreachable.png',
                                             name='Python library pyHS100 missing.',
                                             description="Run 'pip install pyHS100 --user' from a terminal.",
                                             on_enter=ExtensionCustomAction('',
                                             keep_app_open=True)))
        else:
            if plug_name_list:
                for ip in plug_name_list:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((ip, int(9999)))
                        s.shutdown(2)
                        plug = p.SmartPlug(ip)

                        plug_desc = plug.hw_info['dev_name']
                        plug_feature = plug.get_sysinfo()['feature']

                        if plug.state == "OFF":
                            plug_state = "OFF"
                            opposite_state = "On"
                            plug_icon = 'images/icon_off.png'
                        elif plug.state == "ON":
                            plug_since = plug.on_since
                            now = datetime.datetime.now()
                            diff = now - plug_since
                            diff_display = diff.seconds / 60
                            
                            if plug_feature == "TIM":
                                plug_state = "ON\nFor " + str(int(diff_display)) + " minutes"
                            elif plug_feature == "TIM:ENE":
                                plug_state = "ON\nFor " + str(int(diff_display)) + " minutes (Current Consumption " + str(plug.current_consumption()) + " w)"

                            opposite_state = "Off"
                            plug_icon = 'images/icon_on.png'

                        data = {'new_name': 'Turning ' + opposite_state + ' ' + plug.alias + '!',
                                'device_type': 'plug',
                                'target': ip, 
                                'desired_state': opposite_state}

                        if extension.preferences["debug"] == "False":
                            items.append(ExtensionResultItem(icon=plug_icon,
                                                            name='%s' % (plug.alias),
                                                            description='%s - %s\n\nCurrent State %s' % (plug_desc, plug.model, plug_state),
                                                            on_enter=ExtensionCustomAction(data, keep_app_open=True)))
                        else:
                            items.append(ExtensionResultItem(icon=plug_icon,
                                                            name='%s' % (plug.alias),
                                                            description='%s - %s\n\nCurrent State %s\nIP %s' % (plug_desc, plug.model, plug_state, ip),
                                                            on_enter=ExtensionCustomAction(data, keep_app_open=True)))

                    except:
                        logger.info('Failed to communicate with device.')

                        data = {'new_name': 'Failed to communicate with Smart Plug ' + plug.alias
                            }

                        items.append(ExtensionResultItem(icon='images/icon_unreachable.png',
                                                        name='Smart Plug %s is not reachable.' % ip,
                                                        on_enter=ExtensionCustomAction(data, keep_app_open=False)))

            if bulb_name_list:
                for ip in bulb_name_list:
                    try:
                        logging.info("Trying connection with Smart Bulb " + ip)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((ip, int(9999)))
                        s.shutdown(2)
                        bulb = p.SmartBulb(ip)

                        bulb_desc = bulb.get_sysinfo()["description"]

                        if bulb.state == "OFF":
                            bulb_state = "OFF"
                            opposite_state = "On"
                            bulb_icon = 'images/bulb_off.png'
                        elif bulb.state == "ON":
                            bulb_state = "ON\nCurrent Consumption " + str(bulb.current_consumption()) + " w"
                            opposite_state = "Off"
                            bulb_icon = 'images/bulb_on.png'

                        data = {'new_name': 'Turning ' + opposite_state + ' ' + bulb.alias + '!',
                                'device_type': 'bulb',
                                'target': ip, 
                                'desired_state': opposite_state}

                        if extension.preferences["debug"] == "False":
                            items.append(ExtensionResultItem(icon=bulb_icon,
                                                            name='%s' % (bulb.alias),
                                                            description='%s - %s\n\nCurrent State %s' % (bulb_desc, bulb.model, bulb_state),
                                                            on_enter=ExtensionCustomAction(data, keep_app_open=True)))
                        else:
                            items.append(ExtensionResultItem(icon=bulb_icon,
                                                            name='%s' % (bulb.alias),
                                                            description='%s - %s\n\nCurrent State %s\nIP %s' % (bulb_desc, bulb.model, bulb_state, ip),
                                                            on_enter=ExtensionCustomAction(data, keep_app_open=True)))

                    except:
                        logger.info('Failed to communicate with device.')

                        data = {'new_name': 'Failed to communicate with Smart bulb ' + bulb.alias
                            }

                        items.append(ExtensionResultItem(icon='images/bulb_unreachable.png',
                                                        name='Smart Bulb %s is not reachable.' % ip,
                                                        on_enter=ExtensionCustomAction(data, keep_app_open=False)))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):

        import pyHS100 as p

        data = event.get_data()

        if data['device_type'] == "plug":
            dev = p.SmartPlug(data['target'])
        elif data['device_type'] == "bulb":
            dev = p.SmartBulb(data['target'])

        if data['desired_state'] == "On":
            dev.turn_on()
            plug_icon = 'images/icon_on.png'
        elif data['desired_state'] == "Off":
            dev.turn_off()
            plug_icon = 'images/icon_off.png'

        return RenderResultListAction([ExtensionResultItem(icon=plug_icon,
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


if __name__ == '__main__':
    DemoExtension().run()
