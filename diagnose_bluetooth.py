
import asyncio
from datetime import datetime

from winrt.windows.devices.bluetooth import BluetoothLEDevice
from winrt.windows.devices.enumeration import DeviceInformation

MOUSE_NAME = "BT5.0 Mouse"
REFRESH_SECONDS = 3


async def main():
    mouse = None

    print("=" * 55)
    print("       METOO BLUETOOTH CONNECTION DIAGNOSTIC")
    print("=" * 55)

    try:
        print("\nSearching for METOO mouse...")

        selector = BluetoothLEDevice.get_device_selector()
        devices = await DeviceInformation.find_all_async_aqs_filter(
            selector
        )

        mouse_info = next(
            (device for device in devices if device.name == MOUSE_NAME),
            None
        )

        if mouse_info is None:
            print("\nMouse not found.")
            return

        print(f"\nDevice found: {mouse_info.name}")
        print(f"Device ID: {mouse_info.id}")

        mouse = await BluetoothLEDevice.from_id_async(mouse_info.id)

        if mouse is None:
            print("\nCould not open Bluetooth device.")
            return

        print("\nMonitoring connection...")
        print("Switch your mouse OFF and ON to test.")
        print("Press CTRL+C to stop.\n")

        previous_status = None

        while True:
            status = int(mouse.connection_status)

            if status != previous_status:
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Corrected colour mapping
                if status == 1:
                    print(f"[{timestamp}] GREEN - CONNECTED")
                elif status == 0:
                    print(f"[{timestamp}] RED - DISCONNECTED")
                else:
                    print(f"[{timestamp}] UNKNOWN STATUS: {status}")

                previous_status = status

            await asyncio.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\nDiagnostic stopped.")

    except asyncio.CancelledError:
        print("\nDiagnostic stopped.")

    except Exception as error:
        print(f"\nDiagnostic error: {type(error).__name__}: {error}")

    finally:
        if mouse is not None:
            mouse.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
