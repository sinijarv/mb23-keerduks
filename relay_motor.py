import asyncio
from gpiozero import OutputDevice

# Motor class, which is not driven by H-bridge, but just 2 SPDT relays
class RelayMotor:
    def __init__(self, pin1, pin2) -> None:
        self.relay1_pin = OutputDevice(pin1, active_high=False)
        self.relay2_pin = OutputDevice(pin2, active_high=False)
        
    
    async def forward(self) -> None:
        self.relay1_pin.on()
        self.relay2_pin.off()
        await asyncio.sleep(0.2)
        
        
    async def backward(self) -> None:
        self.relay1_pin.off()
        self.relay2_pin.on()
        await asyncio.sleep(0.2)
        
        
    def stop(self) -> None:
        self.relay1_pin.off()
        self.relay2_pin.off()