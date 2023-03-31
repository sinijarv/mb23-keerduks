import usb.core

# Barcode reader class, which sends its data over usb
class BarcodeReader:
    def __init__(self, vendor_id, product_id) -> None:
        dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        self.endpoint = dev[0][(0, 0)][0]
        pass
    
    
    def read(self) -> str:
        return self.endpoint.read(self.endpoint.wMaxPacketSize, timeout=0)
