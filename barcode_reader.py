import usb.core
import usb.util
import asyncio
import requests
import struct


# Barcode reader class, which sends its data over usb
class BarcodeReader:
    def __init__(self, device) -> None:
        self.data_ready = False
        self.dev = device
        
        if self.dev is None:
            raise ValueError('Device not found')

        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)
        self.endpoint = self.dev[0][(0,0)][0]
    
    
    async def read(self) -> None:
        data: list = []
        while True:
            try:
                reading = self.dev.read(self.endpoint.bEndpointAddress,
                    self.endpoint.wMaxPacketSize, 100).tolist()[2]
                data.append(reading)
            except:
                if len(data) > 0:
                    print(data)
                    await self.authorize(data)
                    data = []
            
            await asyncio.sleep(0.02)
            
            
    async def authorize(self, barcode):
        num_bytes = len(barcode)
        format_string = f"{num_bytes}B"
        packed_data = struct.pack(format_string, *barcode)
        
        response = requests.get('http://example.com', params={'data': packed_data})
        
        if response.status_code == 200:
            content = response.text
            if content == 'accepted':
                self.data_ready = True
                
        # To allow all swipes uncomment this
        #self.data_ready = True
        
        
    def is_ready(self) -> bool:
        ret = self.data_ready
        self.data_ready = False
        return ret
        