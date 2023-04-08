import asyncio
import requests
import struct
import logging
import sys

# Configure logging with a custom format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Barcode reader class, which sends its data over usb
class BarcodeReader:
    def __init__(self, device, dir, c) -> None:
        self.data_ready = False
        self.dev = device
        self.dir = dir
        self.authorized_barcode = None
        self.controller = c
        
        if self.dev is None:
            raise ValueError('Device not found')

        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)
        self.endpoint = self.dev[0][(0,0)][0]
    
    
    async def read(self) -> None:
        while True:
            if self.controller.current_state != self.controller.state.LOCKED.value:
                await asyncio.sleep(0.5)
                continue
            try:
                reading = list(self.dev.read(self.endpoint.bEndpointAddress,
                    self.endpoint.wMaxPacketSize, 10))
                if reading:
                    barcode_chars = []
                    for charcode in reading:
                        if ord('0') <= charcode <= ord('9'):
                            barcode_chars.append(chr(charcode))
                    barcode = "".join(barcode_chars)
                    logging.debug(f'Read a card: {barcode}')
                    await self.authorize(barcode)

            except:
                pass
            await asyncio.sleep(0.02)
            
            
    async def authorize(self, barcode):
        response = requests.get('http://10.0.0.10/gate_api.php', params={'kaart': barcode, 'dir': self.dir, 'verbose': 1})
        
        if response.status_code == 200:
            content = response.text
            logging.info(content)
            if content.startswith('OK'):
                self.authorized_barcode = barcode
                self.data_ready = True
                
        # To allow all swipes uncomment this
        #self.data_ready = True
        
        
    def is_ready(self) -> bool:
        ret = self.data_ready
        self.data_ready = False
        return ret
        