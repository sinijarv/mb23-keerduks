#!/usr/bin/python

import asyncio

from gpiozero import LED, Button
from relay_motor import RelayMotor
#from barcode_reader import BarcodeReader

async def main():
    # Declare motor objects for handling incoming and outgoing people
    in_motor = RelayMotor("GPIO17", "GPIO27")
    out_motor = RelayMotor("GPIO23", "GPIO24")
    
    # Declare led objects to indicate the moving direction of the gate
    in_led = LED("GPIO5", active_high=False)
    out_led = LED("GPIO6", active_high=False)
    stop_led = LED("GPIO13", active_high=False, initial_value=True)
    
    # Declare barcode readers for reading incoming and outgoing cards
    #in_barcode = BarcodeReader(vendor_id=0x05e0, product_id=0x1200)
    #out_barcode = BarcodeReader(0x1, 0x2)
    
    # Declare button objects to handle overriding the gate control
    in_button = Button("GPIO19")
    out_button = Button("GPIO26")
    
    #asyncio.create_task(in_barcode.read())
    stop_led.on()
    while True:
        in_motor.forward()
        out_motor.forward()
        await asyncio.sleep(2)
        in_motor.backward()
        out_motor.backward()
        await asyncio.sleep(2)
        in_motor.stop()
        out_motor.stop()
        await asyncio.sleep(2)

asyncio.run(main())
