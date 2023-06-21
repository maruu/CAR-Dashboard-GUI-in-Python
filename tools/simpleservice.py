#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import logging
import socket
import random

from someip.sd import ServiceDiscoveryProtocol
from someip.service import SimpleEventgroup, SimpleService

LOG = logging.getLogger("simpleservice")


class TimeEvgrp(SimpleEventgroup):
    def __init__(self, service: Prot):
        super().__init__(service, id=1, interval=1)
        self.service: Prot

        self.update_task = asyncio.create_task(self.update())

    async def update(self):
        while True:
            self.values[0x0001] = (random.randint(0,100)).to_bytes(1, byteorder='big')
            self.values[0x0002] = (random.randint(0,6)).to_bytes(1, byteorder='big')
            await asyncio.sleep(0.9)


class Prot(SimpleService):
    service_id = 0xB0A7
    version_major = 1
    version_minor = 0

    def __init__(self, instance_id):
        super().__init__(instance_id)
        self.register_eventgroup(TimeEvgrp(self))


async def run(local_addr, multicast_addr, port):

    sd_trsp_u, sd_trsp_m, sd_prot = await ServiceDiscoveryProtocol.create_endpoints(
        family=socket.AF_INET, local_addr=local_addr, multicast_addr=multicast_addr
    )
    sd_prot.timings.CYCLIC_OFFER_DELAY = 2

    prot = await Prot.start_datagram_endpoint(
        instance_id=1, announcer=sd_prot.announcer, local_addr=(local_addr, port)
    )

    sd_prot.start()

    try:
        while True:
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        pass
    finally:
        sd_prot.stop()
        sd_trsp_u.close()
        sd_trsp_m.close()
        prot.stop()


def setup_log(fmt="", **kwargs):
    try:
        import coloredlogs  # type: ignore[import]

        coloredlogs.install(fmt="%(asctime)s,%(msecs)03d " + fmt, **kwargs)
    except ModuleNotFoundError:
        logging.basicConfig(format="%(asctime)s " + fmt, **kwargs)
        logging.info("install coloredlogs for colored logs :-)")


def main():
    setup_log(level=logging.INFO, fmt="%(levelname)-8s %(name)s: %(message)s")
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("local")
    parser.add_argument("--multicast", required=True)
    parser.add_argument("--port", type=int, default=38510)

    args = parser.parse_args()

    try:
        asyncio.get_event_loop().run_until_complete(
            run(args.local, args.multicast, args.port)
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
