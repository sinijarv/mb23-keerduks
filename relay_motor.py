from gpiozero import OutputDevice

# Motor class, which is not driven by H-bridge, but just 2 SPDT relays
class RelayMotor:
    def __init__(self, pin1, pin2) -> None:
        self.relay1_pin = OutputDevice(pin1, active_high=False)
        self.relay2_pin = OutputDevice(pin2, active_high=False)
        
    
    def forward(self) -> None:
        self.relay1_pin.on()
        self.relay2_pin.off()
        
        
    def backward(self) -> None:
        self.relay1_pin.off()
        self.relay2_pin.on()
        
        
    def stop(self) -> None:
        self.relay1_pin.off()
        self.relay2_pin.off()