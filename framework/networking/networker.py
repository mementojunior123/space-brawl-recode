import pygame
from typing import Any, TypedDict, Callable
from types import SimpleNamespace
import platform

class Networker:
    MESSAGE_ENDER : str = "~&|^"
    NETWORK_RECEIVE_EVENT = pygame.event.custom_type()
    NETWORK_ERROR_EVENT = pygame.event.custom_type()
    NETWORK_CONNECTION_EVENT = pygame.event.custom_type()
    NETWORK_DISCONNECT_EVENT = pygame.event.custom_type()
    NETWORK_CLOSE_EVENT = pygame.event.custom_type()

    def __init__(self, core_object_reference : "Core") -> None:
        global core_object
        core_object = core_object_reference
        self.core : "Core" = core_object
        self.NETWORK_LOCALSTORAGE_KEYS : list[str] = []
        if "networking" not in self.core.js_source:
            self.core.load_js_source_file("framework/networking/networking.js", "networking", 
                                            {"PEERID" : None, "IS_HOST" : None, "NETWORK_KEY" : None,
                                             "DEBUG_LEVEL" : None})
        if "sendnetmessage" not in self.core.js_source:
            self.core.load_js_source_file("framework/networking/network_send_event_dispatcher.js", "sendnetmessage", 
                                            {"DATA" : None, "NETWORK_KEY" : None})
        if "destroynet" not in self.core.js_source:
            self.core.load_js_source_file("framework/networking/network_close_event_dispatcher.js", 'destroynet',
                                          {"NETWORK_KEY" : None})
        
    def update_network_recv(self):
        mods : dict[str, Callable[[SimpleNamespace], None]] = {
            "recv" : self.on_data_received,
            "err" : self.on_network_error,
            "conn" : self.on_network_connection,
            "close" : self.on_network_close,
            "dc" : self.on_network_disconnect
        }
        for net_key in self.NETWORK_LOCALSTORAGE_KEYS:
            for mod in mods:
                curr_recv : str|None = self.core.storage.get_web(net_key + mod)
                if curr_recv:
                    for chunk in curr_recv.split(self.MESSAGE_ENDER):
                        if not chunk:
                            continue
                        callback = mods[mod]
                        callback(SimpleNamespace(detail={'data' : chunk, 'net_key' : net_key}))
                    self.core.storage.set_web(net_key + mod, "")
    
    def create_peer(self, peer_id : str, is_host : str, network_key : str, debug_level : int = 2):
        self.NETWORK_LOCALSTORAGE_KEYS.append(network_key)
        core_object.run_js_source_file("networking", {"PEERID" : peer_id, "IS_HOST" : is_host,
                                                      "NETWORK_KEY" : network_key,
                                                      "DEBUG_LEVEL" : str(debug_level)})
    
    def destroy_peer(self, network_key : str):
        if network_key in self.NETWORK_LOCALSTORAGE_KEYS:
            self.NETWORK_LOCALSTORAGE_KEYS.remove(network_key)
        core_object.run_js_source_file("destroynet", {"NETWORK_KEY" : network_key})
        self.core.log('hello')
        
    
    def on_data_received(self, event : SimpleNamespace):
        #print(event.detail)
        pygame.event.post(pygame.Event(self.NETWORK_RECEIVE_EVENT, 
                                {'data' : event.detail['data'], 'network_key' : event.detail['net_key']}))

    def on_network_error(self, event : SimpleNamespace):
        #print(event.detail)
        pygame.event.post(pygame.Event(self.NETWORK_ERROR_EVENT, 
                                       {'info' : event.detail['data'], 'network_key' : event.detail['net_key']}))

    def on_network_connection(self, event : SimpleNamespace):
        pygame.event.post(pygame.Event(self.NETWORK_CONNECTION_EVENT, 
                                       {'network_key' : event.detail['net_key']}))

    def on_network_close(self, event : SimpleNamespace):
        pygame.event.post(pygame.Event(self.NETWORK_CLOSE_EVENT, 
                                       {'network_key' : event.detail['net_key']}))

    def on_network_disconnect(self, event : SimpleNamespace):
        pygame.event.post(pygame.Event(self.NETWORK_DISCONNECT_EVENT, 
                                       {'network_key' : event.detail['net_key']}))

    def send_network_message(self, data : str, network_key : str) -> bool:
        return self.core.run_js_source_file("sendnetmessage", {"DATA" : data, "NETWORK_KEY" : network_key})

    def update(self):
        if self.core.is_web():
            self.update_network_recv()
    
    def __hints(self):
        global Core
        from framework.core.core import Core, JsSource

