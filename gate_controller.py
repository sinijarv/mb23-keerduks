from __future__ import annotations # For nested class type hinting

from gpiozero import LED, Button, DigitalInputDevice

from state_machine_base import State, StateMachine
from relay_motor import RelayMotor
from barcode_reader import BarcodeReader


class GateController(StateMachine):
    class IdleState(State):
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
                self.controller.set_state(self.controller.enter_state)
                return
            
            if self.controller.out_barcode.is_ready():
                self.controller.set_state(self.controller.exit_state)
                return
            
            if self.controller.in_button.is_active:
                self.controller.set_state(self.controller.free_enter_state)
                return
                      
            if self.controller.out_button.is_active:
                self.controller.set_state(self.controller.free_exit_state)
                return
            
            
        async def on_exit(self) -> None:
            pass
            

    class EnterState(State):
        pass


    class ExitState(State):
        pass


    class FreeEnterState(State):
        pass


    class FreeExitState(State):
        pass
    
    def __init__(self) -> None:
        # Declare motor objects for handling incoming and outgoing people
        self.in_motor = RelayMotor("GPIO17", "GPIO27")
        self.out_motor = RelayMotor("GPIO23", "GPIO24")
        
        # Declare phototransistor objects which detect, when the motors can be returned to position
        self.in_phototransistor = DigitalInputDevice() #TODO: Add pin!
        self.out_phototransistor = DigitalInputDevice() #TODO: Add pin!

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
        self.idle_state: State = self.IdleState(self)
        self.enter_state: State = self.EnterState(self)
        self.exit_state: State = self.ExitState(self)
        self.free_enter_state: State = self.FreeEnterState(self)
        self.free_exit_state: State = self.FreeExitState(self)
        
        self.current_state: State = self.IdleState(self)
        self.prev_state: State = self.IdleState(self)
    