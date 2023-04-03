#!/usr/bin/python

import asyncio

from gate_controller import GateController

async def main():
    controller = GateController()
    
    asyncio.create_task(controller.in_barcode.read())
    asyncio.create_task(controller.out_barcode.read())

    while True:
        controller.run()
        await asyncio.sleep(0.1)

asyncio.run(main())
