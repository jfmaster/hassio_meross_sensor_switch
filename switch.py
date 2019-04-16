import logging

import asyncio

from datetime import timedelta
from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchDevice
from custom_components.meross import (DOMAIN as DOMAIN, MEROSS_DEVICES_BY_ID, MEROSS_DEVICE, HA_SWITCH, MerossDevice)

""" Is it necessary??? """
SCAN_INTERVAL = timedelta(seconds=10)

l = logging.getLogger("meross_switch")
l.setLevel(logging.DEBUG)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

    #l.debug('async_setup_platform called')

    """Set up Meross Switch device."""
    if discovery_info is None:
        return

    ha_entities = []
    meross_device_ids = discovery_info.get('meross_device_ids')
    for meross_device_id in meross_device_ids:
        if meross_device_id in hass.data[DOMAIN][MEROSS_DEVICES_BY_ID]:
            meross_device = hass.data[DOMAIN][MEROSS_DEVICES_BY_ID][meross_device_id][MEROSS_DEVICE]
            meross_device_info = str(meross_device)
            """ Some devices also have a dedicated channel for USB """
            usb_channel = meross_device.get_usb_channel_index()
            """ Some Meross devices return 0 channels... """
            channels = max(1, len(meross_device.get_channels()))
            for channel in range(0, channels):
                suffix = ''
                if channel > 0:
                    suffix = '_'+str(channel)
                if usb_channel is not None:
                    if usb_channel == channel:
                        suffix = '_usb'
                ha_entities.append(MerossSwitch(hass, meross_device_id, meross_device_info, channel, suffix))
    async_add_entities(ha_entities, update_before_add=False)

    #l.debug('async_setup_platform terminated')


class MerossSwitch(MerossDevice, SwitchDevice):
    """meross Switch Device."""

    def __init__(self, hass, meross_device_id, meross_device_info, channel, suffix):
        """Init Meross switch device."""
        switch_id = "{}_{}{}".format(DOMAIN, meross_device_id, suffix)
        super().__init__(hass, meross_device_id, ENTITY_ID_FORMAT, switch_id)
        l.debug('Entity ' + self.entity_id + ' created')
        self._is_on = False
        self.channel = channel
        self._name = meross_device_info.split('(')[0].rstrip()

    async def async_execute_switch_and_set_status(self):
        l.debug(self._name + ' >>> async_execute_switch_and_set_status() called')
        device = self.get_device()
        if device is not None:
            if self._is_on:
                device.turn_on_channel(self.channel)
            else:
                device.turn_off_channel(self.channel)
            if self.meross_device_id in self.hass.data[DOMAIN][MEROSS_DEVICES_BY_ID]:
                self.hass.data[DOMAIN][MEROSS_DEVICES_BY_ID][self.meross_device_id][HA_SWITCH][
                    self.channel] = self._is_on

    async def async_turn_on(self):
        self._is_on = True
        l.debug(self._name+' >>> async_turn_on() called')
        await self.async_execute_switch_and_set_status()

    async def async_turn_off(self):
        self._is_on = False
        l.debug(self._name+' >>> async_turn_off() called')
        await self.async_execute_switch_and_set_status()

    """ OVERIDING """
    async def async_update(self):
        l.debug(self._name+' >>> async_update() called')
        """ update is done in the update function"""
        if self.meross_device_id in self.hass.data[DOMAIN][MEROSS_DEVICES_BY_ID]:
            if self.channel in self.hass.data[DOMAIN][MEROSS_DEVICES_BY_ID][self.meross_device_id][HA_SWITCH]:
                self._is_on = self.hass.data[DOMAIN][MEROSS_DEVICES_BY_ID][self.meross_device_id][HA_SWITCH][self.channel]

    """ Ref: https://developers.home-assistant.io/docs/en/entity_index.html """

    @property
    def name(self):
        """Name of the device."""
        return self._name

    @property
    def is_on(self):
        l.debug(self._name+' >>> is_on() called')
        return self._is_on

