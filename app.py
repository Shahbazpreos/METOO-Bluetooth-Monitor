
"""
METOO Bluetooth Monitor
A lightweight Windows system-tray utility for monitoring a METOO Bluetooth mouse.

Dev: Shabbi
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional

import pystray
from PIL import Image, ImageDraw
from winotify import Notification, audio
from winreg import (
    HKEY_CURRENT_USER, KEY_READ, SetValueEx,
    DeleteValue, REG_SZ, CreateKey, OpenKey
)
from winrt.windows.devices.bluetooth import BluetoothLEDevice
from winrt.windows.devices.enumeration import DeviceInformation

APP_NAME = "METOO Bluetooth Monitor"
DEVICE_NAME = "BT5.0 Mouse"
DEVICE_ADDRESS = "e2:07:5e:f8:69:a1"

POLL_SECONDS = 3
INITIAL_RETRIES = 4
INITIAL_RETRY_SECONDS = 1.5

STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_VALUE_NAME = "METOOBluetoothMonitor"

BASE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "METOO-Battery-Monitor"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def startup_command() -> str:
    if is_frozen():
        return f'"{Path(sys.executable).resolve()}"'
    return f'"{Path(sys.executable).resolve()}" "{Path(__file__).resolve()}"'


def startup_enabled() -> bool:
    try:
        with OpenKey(HKEY_CURRENT_USER, STARTUP_REG_PATH, 0, KEY_READ) as key:
            value, _ = __import__("winreg").QueryValueEx(key, STARTUP_VALUE_NAME)
            return bool(value)
    except OSError:
        return False


def set_startup(enabled: bool) -> None:
    with CreateKey(HKEY_CURRENT_USER, STARTUP_REG_PATH) as key:
        if enabled:
            SetValueEx(key, STARTUP_VALUE_NAME, 0, REG_SZ, startup_command())
        else:
            try:
                DeleteValue(key, STARTUP_VALUE_NAME)
            except FileNotFoundError:
                pass


def make_icon_image(connected: Optional[bool], size: int = 64) -> Image.Image:
    """Draw the mouse icon. None means the app is still checking."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = size * 0.20
    body = (margin, size * 0.08, size - margin, size - size * 0.08)

    draw.rounded_rectangle(
        body,
        radius=size * 0.28,
        fill=(37, 43, 54, 255),
        outline=(205, 213, 224, 255),
        width=max(2, size // 24),
    )

    draw.line(
        (size / 2, size * 0.12, size / 2, size * 0.45),
        fill=(205, 213, 224, 255),
        width=max(2, size // 24),
    )

    draw.line(
        (size / 2, size * 0.34, size / 2, size * 0.55),
        fill=(205, 213, 224, 255),
        width=max(2, size // 32),
    )

    if connected is True:
        color = (46, 204, 113, 255)       # Green
    elif connected is False:
        color = (231, 76, 60, 255)        # Red
    else:
        color = (241, 196, 15, 255)       # Amber / checking

    dot = (size * 0.64, size * 0.64, size * 0.96, size * 0.96)

    draw.ellipse(
        dot,
        fill=color,
        outline=(20, 24, 31, 255),
        width=max(2, size // 24),
    )

    return image


class MouseMonitor:
    """
    Monitors the METOO mouse using WinRT BluetoothLEDevice.

    Verified status mapping for this mouse:
        1 = Connected
        0 = Disconnected
    """

    def __init__(self, on_change):
        self.on_change = on_change
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._device: Optional[BluetoothLEDevice] = None
        self._connected: Optional[bool] = None
        self._device_id: Optional[str] = None

    @property
    def connected(self) -> Optional[bool]:
        return self._connected

    @property
    def device_id(self) -> Optional[str]:
        return self._device_id

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _thread_main(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._monitor())
        except Exception:
            logging.exception("Bluetooth monitor thread failed")
        finally:
            if self._device is not None:
                try:
                    self._device.close()
                except Exception:
                    logging.exception("Could not close Bluetooth device")

            pending = asyncio.all_tasks(self._loop)

            for task in pending:
                task.cancel()

            try:
                self._loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            except Exception:
                pass

            self._loop.close()

    async def _find_device(self):
        selector = BluetoothLEDevice.get_device_selector()
        devices = await DeviceInformation.find_all_async_aqs_filter(selector)

        matches = [
            device for device in devices
            if device.name == DEVICE_NAME
        ]

        if not matches:
            return None

        for item in matches:
            if DEVICE_ADDRESS.replace(":", "").lower() in item.id.lower():
                return item

        return matches[0]

    async def _open_device(self) -> bool:
        """Find and open a fresh Bluetooth device object."""
        info = await self._find_device()

        if info is None:
            logging.info("Mouse not found during device discovery")
            return False

        self._device_id = info.id
        self._device = await BluetoothLEDevice.from_id_async(info.id)

        if self._device is None:
            logging.warning("Windows could not open the Bluetooth device")
            return False

        logging.info("Monitoring device: %s (%s)", info.name, info.id)
        return True

    async def _initial_connection_check(self) -> Optional[bool]:
        """
        Verify the initial status.

        Windows can briefly return a stale disconnected status when the
        Bluetooth device object is first created. If that happens, reopen
        the device and check again before deciding it is disconnected.
        """
        for attempt in range(1, INITIAL_RETRIES + 1):
            if self._stop.is_set():
                return None

            if self._device is None:
                try:
                    opened = await self._open_device()
                except Exception:
                    logging.exception("Initial Bluetooth discovery failed")
                    opened = False

                if not opened:
                    if attempt < INITIAL_RETRIES:
                        await asyncio.sleep(INITIAL_RETRY_SECONDS)
                        continue
                    return None

            # Give Windows a moment to populate the connection status.
            await asyncio.sleep(INITIAL_RETRY_SECONDS)

            if self._device is None:
                continue

            raw_status = int(self._device.connection_status)
            logging.info(
                "Initial connection check %s/%s: raw status=%s",
                attempt,
                INITIAL_RETRIES,
                raw_status,
            )

            if raw_status == 1:
                return True

            if raw_status == 0 and attempt < INITIAL_RETRIES:
                # A fresh device object may receive a more current status.
                try:
                    self._device.close()
                except Exception:
                    pass

                self._device = None
                await asyncio.sleep(0.5)

        # All initial checks reported disconnected.
        if self._device is not None:
            return int(self._device.connection_status) == 1

        return None

    async def _monitor(self) -> None:
        initial_check_complete = False

        while not self._stop.is_set():
            try:
                if self._device is None:
                    opened = await self._open_device()

                    if not opened:
                        self._set_state(None, "Mouse not found")
                        await asyncio.sleep(POLL_SECONDS)
                        continue

                if not initial_check_complete:
                    connected = await self._initial_connection_check()

                    if self._stop.is_set():
                        break

                    if connected is None:
                        self._set_state(None, "Searching")
                        await asyncio.sleep(POLL_SECONDS)
                        continue

                    initial_check_complete = True
                    self._set_state(
                        connected,
                        "Connected" if connected else "Disconnected",
                    )

                else:
                    # Normal monitoring after the initial check.
                    raw_status = int(self._device.connection_status)
                    connected = (raw_status == 1)

                    if connected != self._connected:
                        self._set_state(
                            connected,
                            "Connected" if connected else "Disconnected",
                        )

                await asyncio.sleep(POLL_SECONDS)

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                logging.exception("Bluetooth polling error: %s", exc)

                self._set_state(None, "Monitoring error")

                if self._device is not None:
                    try:
                        self._device.close()
                    except Exception:
                        pass

                    self._device = None

                # If an error happened during initial startup, try the
                # initial verification process again.
                await asyncio.sleep(POLL_SECONDS)

    def _set_state(self, connected: Optional[bool], label: str) -> None:
        changed = connected != self._connected
        self._connected = connected

        if changed:
            self.on_change(connected, label)


class TrayApplication:
    def __init__(self):
        self.icon: Optional[pystray.Icon] = None
        self.monitor = MouseMonitor(self._on_state_change)
        self._last_notification_state: Optional[bool] = None

    def _notify(self, title: str, message: str) -> None:
        try:
            toast = Notification(
                app_id=APP_NAME,
                title=title,
                msg=message,
                duration="short",
            )

            toast.set_audio(audio.Default, loop=False)
            toast.show()

        except Exception:
            logging.exception("Notification could not be displayed")

    def _on_state_change(
        self,
        connected: Optional[bool],
        label: str,
    ) -> None:
        logging.info("Mouse state changed: %s", label)

        if self.icon is not None:
            try:
                self.icon.icon = make_icon_image(connected)
                self.icon.title = f"{APP_NAME} — {label}"
                self.icon.update_menu()
            except Exception:
                logging.exception("Could not update tray icon")

        # Do not notify for the initial state or unknown states.
        if connected is not None:
            if self._last_notification_state is not None:
                if connected != self._last_notification_state:
                    if connected:
                        self._notify(
                            "Mouse connected",
                            "Your METOO mouse is connected.",
                        )
                    else:
                        self._notify(
                            "Mouse disconnected",
                            "Your METOO mouse has disconnected.",
                        )

            self._last_notification_state = connected

    def _status_text(self, _item=None) -> str:
        state = self.monitor.connected

        if state is True:
            return "Status: Connected"

        if state is False:
            return "Status: Disconnected"

        return "Status: Searching..."

    def _toggle_startup(self, _icon, _item) -> None:
        enabled = not startup_enabled()

        try:
            set_startup(enabled)

            self._notify(
                "Startup setting updated",
                "METOO Monitor will start with Windows."
                if enabled
                else "METOO Monitor will no longer start with Windows.",
            )

            if self.icon:
                self.icon.update_menu()

        except Exception:
            logging.exception("Could not change startup setting")
            self._notify(
                "Startup setting failed",
                "Could not update the Windows startup setting.",
            )

    def _quit(self, icon, _item) -> None:
        self.monitor.stop()
        icon.stop()

    def run(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem(
                self._status_text,
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Device: BT5.0 Mouse",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                "Start with Windows",
                self._toggle_startup,
                checked=lambda _item: startup_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

        # Start with amber while the first Bluetooth check is running.
        self.icon = pystray.Icon(
            "metoo_bluetooth_monitor",
            make_icon_image(None),
            APP_NAME,
            menu,
        )

        self.monitor.start()
        self.icon.run()


def main() -> None:
    if os.name != "nt":
        raise SystemExit(
            "METOO Bluetooth Monitor currently supports Windows 10/11 only."
        )

    setup_logging()
    logging.info("Starting %s", APP_NAME)

    app = TrayApplication()

    try:
        app.run()
    except Exception:
        logging.exception("Application crashed")
        raise


if __name__ == "__main__":
    main()
