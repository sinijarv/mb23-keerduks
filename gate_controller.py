from __future__ import annotations # For nested class type hinting

import asyncio
from gpiozero import LED, Button, DigitalInputDevice
from enum import Enum
from time import monotonic
from datetime import timedelta

from state_machine_base import State, StateMachine
from relay_motor import RelayMotor
from barcode_reader import BarcodeReader




class LockedState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        
    
    async def on_enter(self) -> None:
        self.controller.in_motor.stop()
        self.controller.out_motor.stop()
        self.controller.in_led.off()
        self.controller.out_led.off()
        self.controller.stop_led.on()
        
        
    async def step(self) -> None:
        if self.controller.in_barcode.is_ready():
            self.controller.set_state(self.controller.state.ENTER)
            return
        
        
        if self.controller.out_barcode.is_ready():
            self.controller.set_state(self.controller.state.EXIT)
            return
        
        
        if self.controller.in_button.is_active:
            self.controller.set_state(self.controller.state.FREE_ENTER)
            return
        
            
        if self.controller.out_button.is_active:
            self.controller.set_state(self.controller.state.FREE_EXIT)
            return
        
        
    async def on_exit(self) -> None:
        self.controller.stop_led.off()
        
        
class EnterState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        self.start_time = monotonic()
        
        
    async def on_enter(self) -> None:
        self.controller.in_motor.forward()
        self.controller.in_led.on()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            return
        
        # If gate hasn't started moving after time, lock the gate
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED)
            return
            
    
    async def on_exit(self) -> None:
        self.controller.in_led.off()
        self.controller.in_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate


class ExitState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        self.start_time = monotonic()
        
        
    async def on_enter(self) -> None:
        self.controller.out_motor.forward()
        self.controller.out_led.on()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            return
        
        # If gate hasn't started moving after time, lock the gate
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED)
            return
        
    
    async def on_exit(self) -> None:
        self.controller.out_led.off()
        self.controller.out_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate


class FreeEnterState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        self.start_time = monotonic()
        self.toggle_time_elapsed = False

        
    async def on_enter(self) -> None:
        self.controller.in_motor.forward()
        self.controller.in_led.on()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            return
        
        # If button is pressed down, keep the gate open
        if self.controller.in_button.is_active:
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED)
            return
        
    
    async def on_exit(self) -> None:
        self.controller.in_motor.backward()
        await asyncio.sleep(1) # Wait for motor to lock the gate


class FreeExitState(State):
    def __init__(self, ctrlr: GateController) -> None:
        self.controller = ctrlr
        self.start_time = monotonic()
        self.toggle_time_elapsed = False

        
    async def on_enter(self) -> None:
        self.controller.out_motor.forward()
        self.controller.out_led.on()
    
    
    async def step(self) -> None:
        # Person is going through the gate
        if self.controller.is_gate_moving():
            return
        
        # If button is pressed down, keep the gate open
        if self.controller.in_button.is_active:
            return
        
        # In case button was just toggled and state is already inactive, then wait some time
        if (monotonic() > self.start_time + timedelta(seconds=4).seconds):
            self.controller.set_state(self.controller.state.LOCKED)
            return
        
    
    async def on_exit(self) -> None:
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
        self.in_motor = RelayMotor("GPIO17", "GPIO27")
        self.out_motor = RelayMotor("GPIO23", "GPIO24")
        
        # Declare phototransistor objects which detect, when the motors can be returned to position
        self.phototransistor_1 = DigitalInputDevice() #TODO: Add pin!
        self.phototransistor_2 = DigitalInputDevice() #TODO: Add pin!

        # Declare led objects to indicate the moving direction of the gate
        self.in_led = LED("GPIO5", active_high=False)
        self.out_led = LED("GPIO6", active_high=False)
        self.stop_led = LED("GPIO13", active_high=False, initial_value=True)

        # Declare barcode readers for reading incoming and outgoing cards
        self.in_barcode = BarcodeReader(vendor_id=0x05e0, product_id=0x1200)
        self.out_barcode = BarcodeReader(0x1, 0x2)

        # Declare button objects to handle overriding the gate control
        self.in_button = Button("GPIO19")
        self.out_button = Button("GPIO26")
                
        # State machine related variables
        class States(Enum):
            LOCKED = LockedState(self),
            ENTER = EnterState(self),
            EXIT = ExitState(self),
            FREE_ENTER = FreeEnterState(self),
            FREE_EXIT = FreeExitState(self)
        self.state = States()
        
        self.current_state: State = self.state.LOCKED
        self.prev_state: State = self.state.LOCKED
        
    
    def is_gate_moving(self):
        if self.phototransistor_1.is_active or self.phototransistor_2.is_active:
            return True
    