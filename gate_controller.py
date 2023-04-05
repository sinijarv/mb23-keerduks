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
        self.controller.in_motor.forward()
        self.controller.in_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            # TODO: Send moved message to server
            return
        
        # If gate hasn't started moving after time, lock the gate
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
            
    
    async def on_exit(self) -> None:
        logging.info('exiting Enter state')
        self.controller.in_led.off()
        self.controller.in_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate


class ExitState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        
        
    async def on_enter(self) -> None:
        logging.info('entering Exit state')
        self.controller.out_motor.forward()
        self.controller.out_led.on()
        self.start_time = monotonic()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            # TODO: Send moved message to server
            return
        
        # If gate hasn't started moving after time, lock the gate
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
    
    async def on_exit(self) -> None:
        logging.info('exiting Exit state')
        self.controller.out_led.off()
        self.controller.out_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate


class FreeEnterState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr

        
    async def on_enter(self) -> None:
        logging.info('entering Free Enter state')
        self.controller.in_motor.forward()
        self.controller.in_led.on()
        self.start_time = monotonic()
        self.toggle_time_elapsed = False
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            # TODO: Send moved message to server
            return
        
        # If button is pressed down, keep the gate open
        if self.controller.in_button.is_active:
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
    
    async def on_exit(self) -> None:
        logging.info('exiting Free Enter state')
        self.controller.in_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate


class FreeExitState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr

        
    async def on_enter(self) -> None:
        logging.info('entering Free Exit state')
        self.controller.out_motor.forward()
        self.controller.out_led.on()
        self.start_time = monotonic()
        self.toggle_time_elapsed = False
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            # TODO: Send moved message to server
            return
        
        # If button is pressed down, keep the gate open
        if self.controller.in_button.is_active:
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED.value)
            return
        
    
    async def on_exit(self) -> None:
        logging.info('exiting Free Exit state')
        self.controller.out_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate
        
        
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
        self.in_motor = RelayMotor('GPIO17', 'GPIO27')
        self.out_motor = RelayMotor('GPIO23', 'GPIO24')
        
        # Declare phototransistor objects which detect, when the motors can be returned to position
        self.phototransistor_1 = DigitalInputDevice('GPIO20')
        self.phototransistor_2 = DigitalInputDevice('GPIO21')

        # Declare led objects to indicate the moving direction of the gate
        self.in_led = LED('GPIO5', active_high=False)
        self.out_led = LED('GPIO6', active_high=False)
        self.stop_led = LED('GPIO13', active_high=False, initial_value=True)
        
        # Declare button objects to handle overriding the gate control
        self.in_button = Button('GPIO19')
        self.out_button = Button('GPIO26')

        # Declare barcode readers for reading incoming and outgoing cards
        devices = usb.core.find(find_all=True, idVendor=0x05e0, idProduct=0x1200)
        for dev in devices:
            serial = usb.util.get_string(dev, dev.iSerialNumber)[4:36]
            if serial == 'E21478C6B18CE448A31DD361F4A3BCFA':
                self.out_barcode = BarcodeReader(dev)
            if serial == '1270FBD3FECE81458C725FA0C6749F5E':
                self.in_barcode = BarcodeReader(dev)
                
        # State machine related variables
        class States(Enum):
            LOCKED = LockedState(self)
            ENTER = EnterState(self)
            EXIT = ExitState(self)
            FREE_ENTER = FreeEnterState(self)
            FREE_EXIT = FreeExitState(self)
        self.state = States
        
        self.current_state: State = self.state.LOCKED.value
        self.prev_state: State = None
        
    
    def is_gate_moving(self):
        if self.phototransistor_1.is_active or self.phototransistor_2.is_active:
            return True
    