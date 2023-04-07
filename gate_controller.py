from __future__ import annotations # For nested class type hinting

import asyncio
import usb.core
import usb.util

from gpiozero import LED, Button, DigitalInputDevice
from enum import Enum
from time import monotonic
from datetime import timedelta
import logging
import sys
import requests

from state_machine_base import State, StateMachine
from relay_motor import RelayMotor
from barcode_reader import BarcodeReader


# Configure logging with a custom format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)


class LockedState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        
    
    async def on_enter(self) -> None:
        logging.info('entering Locked state')
        await self.controller.in_motor.forward()
        await self.controller.out_motor.forward()
        self.controller.in_motor.stop()
        self.controller.out_motor.stop()
        self.controller.in_led.off()
        self.controller.out_led.off()
        self.controller.stop_led.on()
        
        
    async def step(self) -> None:
        if self.controller.in_barcode.is_ready():
            self.controller.set_state(self.controller.state.ENTER.value)
            return
        
        
        if self.controller.out_barcode.is_ready():
            self.controller.set_state(self.controller.state.EXIT.value)
            return
        
        if self.controller.in_button.is_active and self.controller.out_button.is_active:
            self.controller.set_state(self.controller.state.FREEWHEEL.value)
            return
        
        if self.controller.in_button.is_active:
            self.controller.set_state(self.controller.state.FREE_ENTER.value)
            return
        
            
        if self.controller.out_button.is_active:
            self.controller.set_state(self.controller.state.FREE_EXIT.value)
            return
        
        
    async def on_exit(self) -> None:
        logging.info('exiting Locked state')
        self.controller.stop_led.off()
        
        
class EnterState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        
        
    async def on_enter(self) -> None:
        logging.info('entering Enter state')
        await self.controller.in_motor.backward()
        self.controller.in_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            requests.get('http://10.0.0.108/gate_api.php', params={
                'kaart': self.controller.in_barcode.authorized_barcode,
                'dir': self.controller.in_barcode.dir,
                'passed': 1,
                'verbose': 1})
            self.controller.in_barcode.authorized_barcode = None
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
        # If gate hasn't started moving after time, lock the gate
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
            
    
    async def on_exit(self) -> None:
        logging.info('exiting Enter state')
        self.controller.in_led.off()


class ExitState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        
        
    async def on_enter(self) -> None:
        logging.info('entering Exit state')
        await self.controller.out_motor.backward()
        self.controller.out_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            requests.get('http://10.0.0.108/gate_api.php', params={
                'kaart': self.controller.out_barcode.authorized_barcode,
                'dir': self.controller.out_barcode.dir,
                'passed': 1,
                'verbose': 1})
            self.controller.out_barcode.authorized_barcode = None
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
        # If gate hasn't started moving after time, lock the gate
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
    
    async def on_exit(self) -> None:
        logging.info('exiting Exit state')
        self.controller.out_led.off()


class FreeEnterState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr

        
    async def on_enter(self) -> None:
        logging.info('entering Free Enter state')
        await self.controller.in_motor.backward()
        self.controller.in_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        if self.controller.in_button.is_active and self.controller.out_button.is_active:
            self.controller.set_state(self.controller.state.FREEWHEEL.value)
            return
        
        # If button is pressed down, keep the gate open
        if self.controller.in_button.is_active:
            await asyncio.sleep(0.1)
            return
        
        # Person is going through the gate
        if self.controller.is_gate_moving():
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
    
    async def on_exit(self) -> None:
        logging.info('exiting Free Enter state')


class FreeExitState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr

        
    async def on_enter(self) -> None:
        logging.info('entering Free Exit state')
        await self.controller.out_motor.backward()
        self.controller.out_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        if self.controller.in_button.is_active and self.controller.out_button.is_active:
            self.controller.set_state(self.controller.state.FREEWHEEL.value)
            return
        
        # If button is pressed down, keep the gate open
        if self.controller.out_button.is_active:
            await asyncio.sleep(0.1)
            return
        
        # Person is going through the gate
        if self.controller.is_gate_moving():
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
    
    async def on_exit(self) -> None:
        logging.info('exiting Free Exit state')
        
        
class FreewheelState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr

        
    async def on_enter(self) -> None:
        logging.info('entering Freewheel state')
        await self.controller.in_motor.backward()
        await self.controller.out_motor.backward()
        self.controller.in_led.on()
        self.controller.out_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        # If button is pressed down, keep the gate open
        if self.controller.in_button.is_active and self.controller.out_button.is_active:
            await asyncio.sleep(0.1)
            return
        
        # Either way go through locked state first
        if (self.controller.is_gate_moving() and (not self.controller.in_button.is_active or
                                                  not self.controller.out_button.is_active)):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
    
    
    async def on_exit(self) -> None:
        logging.info('exiting Freewheel state')
        
        
class FaultState(State):
    def __init__(self, ctrlr: GateController) -> None:
        pass
        
    
    async def on_enter(self) -> None:
        pass
    
    
    async def step(self) -> None:
        pass
        
    
    async def on_exit(self) -> None:
        pass
    

class GateController(StateMachine):
    def __init__(self) -> None:
        # Declare motor objects for handling incoming and outgoing people
        self.in_motor = RelayMotor('GPIO23', 'GPIO24')
        self.out_motor = RelayMotor('GPIO17', 'GPIO27')
        
        # Declare phototransistor objects which detect, when the motors can be returned to position
        self.phototransistor_1 = DigitalInputDevice('GPIO20', pull_up=True)
        self.phototransistor_2 = DigitalInputDevice('GPIO21', pull_up=True)

        # Declare led objects to indicate the moving direction of the gate
        self.in_led = LED('GPIO13', active_high=False)
        self.out_led = LED('GPIO5', active_high=False)
        self.stop_led = LED('GPIO06', active_high=False, initial_value=True)
        
        # Declare button objects to handle overriding the gate control
        self.in_button = Button('GPIO19')
        self.out_button = Button('GPIO26')

        # Declare barcode readers for reading incoming and outgoing cards
        devices = usb.core.find(find_all=True, idVendor=0x05e0, idProduct=0x0600)
        for dev in devices:
            serial = usb.util.get_string(dev, dev.iSerialNumber)[4:36]
            if serial == 'E21478C6B18CE448A31DD361F4A3BCFA':
                self.out_barcode = BarcodeReader(dev, 'out', self)
            if serial == '1270FBD3FECE81458C725FA0C6749F5E':
                self.in_barcode = BarcodeReader(dev, 'in', self)
                
        # State machine related variables
        class States(Enum):
            LOCKED = LockedState(self)
            ENTER = EnterState(self)
            EXIT = ExitState(self)
            FREE_ENTER = FreeEnterState(self)
            FREE_EXIT = FreeExitState(self)
            FREEWHEEL = FreewheelState(self)
        self.state = States
        
        self.current_state: State = self.state.LOCKED.value
        self.prev_state: State = None
        
    
    def is_gate_moving(self):
        if not self.phototransistor_1.is_active or not self.phototransistor_2.is_active:
            return True
    