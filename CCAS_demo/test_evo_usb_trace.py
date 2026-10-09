"""Offline regression tests for the first Tecan EVO setup USB command."""

from __future__ import annotations

import unittest

from usb.core import USBError, USBTimeoutError

from pylabrobot.liquid_handling.backends import EVOBackend


class FakeUSB:
    """Record PLR writes without opening a physical USB device."""

    def __init__(self, write_error: USBError | None = None) -> None:
        self.writes: list[bytes] = []
        self.reads = 0
        self.write_error = write_error

    async def write(self, data: bytes, timeout: int | None = None) -> None:
        self.writes.append(data)
        if self.write_error is not None:
            raise self.write_error

    async def read(self, timeout: int | None = None) -> bytes:
        self.reads += 1
        return b"\x02C5\x80\x00"


class EVOUSBTraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_liha_setup_sends_pia_before_any_later_setup_command(self) -> None:
        backend = EVOBackend()
        fake_usb = FakeUSB(write_error=USBError("simulated endpoint pipe error"))
        backend.io = fake_usb  # type: ignore[assignment]

        with self.assertRaises(USBError):
            await backend.setup_arm(EVOBackend.LIHA)

        self.assertEqual(fake_usb.writes, [b"\x02C5PIA\x00"])
        self.assertEqual(fake_usb.reads, 0)

    async def test_liha_setup_timeout_propagates_at_first_pia_write(self) -> None:
        backend = EVOBackend()
        fake_usb = FakeUSB(write_error=USBTimeoutError("simulated write timeout"))
        backend.io = fake_usb  # type: ignore[assignment]

        with self.assertRaises(USBTimeoutError):
            await backend.setup_arm(EVOBackend.LIHA)

        self.assertEqual(fake_usb.writes, [b"\x02C5PIA\x00"])
        self.assertEqual(fake_usb.reads, 0)

    async def test_successful_pia_write_waits_for_response_before_bmx(self) -> None:
        backend = EVOBackend()
        fake_usb = FakeUSB()
        backend.io = fake_usb  # type: ignore[assignment]

        await backend.setup_arm(EVOBackend.LIHA)

        self.assertEqual(fake_usb.writes, [b"\x02C5PIA\x00", b"\x02C5BMX2\x00"])
        self.assertEqual(fake_usb.reads, 2)


if __name__ == "__main__":
    unittest.main()
