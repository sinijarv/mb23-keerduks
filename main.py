#!/usr/bin/python

import asyncio
import signal

from gate_controller import GateController


def handle_sigint():
    loop = asyncio.get_event_loop()
    loop.stop()

async def main():
    controller = GateController()
    
    asyncio.create_task(controller.in_barcode.read())
    asyncio.create_task(controller.out_barcode.read())

    while True:
        await controller.run()
        await asyncio.sleep(0.1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, handle_sigint)
    try:
        loop.run_until_complete(main())
    except RuntimeError as ex:
        print(ex)
    print('Program closed!')