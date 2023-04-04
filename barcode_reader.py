import usb.core
import asyncio

# Barcode reader class, which sends its data over usb
class BarcodeReader:
    def __init__(self, vendor_id, product_id) -> None:
        self.barcode_data = []
        self.data_ready = False
        
        self.dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if self.dev is None:
            raise ValueError('Device not found')

        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)
        self.endpoint = self.dev[0][(0,0)][0]
    
    async def read(self) -> None:
        data: list = []
        while True:
            # Wait until the data has been sent out and flag cleared
            if self.data_ready:
                await asyncio.sleep(1)
                
            reading = self.dev.read(self.endpoint.bEndpointAddress,
                self.endpoint.wMaxPacketSize, 0).tolist()[2]
            data.append(reading)
            
            # TODO: Verify that the real card matches this length
            if len(data) > 16:
                self.barcode_data = data
                self.data_ready = True
                print(self.barcode_data)
                data = []
                
    
    #! Check the use of this function, wonky atm!
    def is_ready(self) -> bool:
        return self.data_ready
