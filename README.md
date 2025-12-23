# MCU Packetizer + PC Depacketizer

This repository contains embedded-side C/C++ code that builds binary sensor packets, and PC-side Python code that parses (“depacketizes”) those packets back into typed values. [conversation_history:0]

## Packet format (on the wire)

Each packet is:

- **Header (3 bytes)**
  - Byte 0: `slave_address` (0–255)
  - Byte 1: `data_type` (type code; one type per packet)
  - Byte 2: `variable_count` (1–255) = number of values in the payload
- **Payload (N bytes)**
  - Contains `variable_count` consecutive values, all of the same type.
  - Maximum payload length is `255 * sizeof(type)` bytes.

Notes:
- Floats/doubles are serialized **little-endian** (least-significant byte first).
- The depacketizer expects payload length to match exactly `variable_count * sizeof(type)`.

## File: `mcu_packetizer.h` / `mcu_packetizer.c`

### Types

- `enum DataType`
  - Defines numeric type codes used in the packet header (e.g., int/float/double).

- `struct SensorPacket`
  - Holds the packet header fields plus a payload buffer and `payload_length` tracking how many payload bytes are currently filled.

- `union DataValue`
  - Utility for converting between `float`/`double` and their raw bytes for payload storage.

### Functions

- `uint8_t get_type_size(DataType type)`
  - Returns the byte-size for the given `DataType` code (e.g., 1 for int8, 4 for float32, 8 for float64).
  - Returns 0 for unknown/unsupported types.

- `int8_t packet_init(SensorPacket* packet, uint8_t slave_addr, DataType type, uint8_t var_count)`
  - Initializes the packet header (`slave_address`, `data_type`, `variable_count`) and resets `payload_length` to 0.
  - Validates basic arguments (e.g., packet pointer and variable count range).

- `int8_t packet_add_int(SensorPacket* packet, uint8_t value)`
  - Appends one integer value to the payload.
  - Fails if the packet’s `data_type` is not `DATA_TYPE_INT`, if the payload is full, or if adding would exceed `variable_count`.

- `int8_t packet_add_float(SensorPacket* packet, float value)`
  - Appends one float32 value to the payload by writing its 4 bytes (little-endian).
  - Fails if the packet’s `data_type` is not `DATA_TYPE_FLOAT`, if the payload is full, or if adding would exceed `variable_count`.

- `int8_t packet_add_double(SensorPacket* packet, double value)`
  - Appends one float64 value to the payload by writing its 8 bytes (little-endian).
  - Fails if the packet’s `data_type` is not `DATA_TYPE_DOUBLE`, if the payload is full, or if adding would exceed `variable_count`.

- `int16_t packet_serialize(const SensorPacket* packet, uint8_t* buffer)`
  - Writes the final “on-the-wire” packet into `buffer` as:
    - 3-byte header, then the payload bytes.
  - Verifies the payload length matches `variable_count * sizeof(type)` before serializing.
  - Returns total serialized length (`3 + payload_length`) or -1 on error.

## File: `example_mcu_usage.cpp`

This file is a demo of how firmware might collect sensor values, create packets, serialize them, and transmit them.

### Functions (demo stubs)

- `uint8_t read_temperature_sensor()`, `uint8_t read_humidity_sensor()`, `uint8_t read_pressure_sensor()`
  - Example “sensor read” functions that return integer-style readings (placeholders for real ADC/I2C/SPI sensor reads).

- `float read_voltage_sensor()`
  - Example float-returning sensor read (placeholder for real measurement code).

- `void transmit_packet(const uint8_t* data, uint16_t length)`
  - Demonstrates where UART/SPI/USB transmission would occur (prints bytes in the demo).

- `int main()`
  - Demonstrates building:
    - One integer packet (3 values).
    - One float packet (2 values).
  - Shows the normal workflow: `packet_init` → `packet_add_*` → `packet_serialize` → `transmit_packet`.

## File: `pc_depacketizer.py`

### Classes / Exceptions

- `class DataType(IntEnum)`
  - Mirrors the MCU `DataType` codes so Python can interpret the header type byte.

- `class DepacketizationError(Exception)`
  - Raised when a packet is malformed (unknown type code, wrong length, etc.).

- `class SensorPacket`
  - Container for a decoded packet:
    - `slave_address`, `data_type`, `variable_count`, and `variables` list.
  - `__repr__` provides a concise developer-friendly string.
  - `__str__` provides a human-readable multi-line view.

### Functions

- `get_type_size(data_type: DataType) -> int`
  - Returns the payload element size for the given `DataType`.
  - Raises `DepacketizationError` for unsupported/unknown codes.

- `depacketize(packet_bytes: Union[bytes, bytearray, str]) -> SensorPacket`
  - Core parser that:
    1. Accepts either raw bytes or a hex string.
    2. Validates minimum size (3-byte header).
    3. Reads header fields (`slave_address`, `type_code`, `variable_count`).
    4. Validates payload length equals `variable_count * sizeof(type)`.
    5. Unpacks values into Python types:
       - int values as integers
       - floats via `struct.unpack('<f', ...)`
       - doubles via `struct.unpack('<d', ...)`
  - Returns a `SensorPacket` object or raises `DepacketizationError`.

- `depacketize_batch(packets_data: List[Union[bytes, str]]) -> List[SensorPacket]`
  - Convenience helper that applies `depacketize` to a list of packets.

### Script usage (`if __name__ == "__main__":`)
- Shows example depacketization from a hex string and from raw bytes.
- Demonstrates expected error handling for malformed packets.

## File: `serial_listener.py`

This is an optional integration helper for reading packets from a serial port (requires `pyserial`).

### Class: `SensorPacketListener`

- `__init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0)`
  - Stores serial configuration and initializes internal state (connection handle, callback, running flag).

- `connect(self) -> bool`
  - Opens the serial port and returns whether the connection succeeded.

- `disconnect(self) -> None`
  - Stops listening and closes the serial port if open.

- `set_callback(self, callback: Callable[[SensorPacket], None]) -> None`
  - Registers a function to be called whenever a valid packet is received and decoded.

- `listen(self) -> None`
  - Blocking loop that:
    - Reads available bytes from serial.
    - Attempts to parse them as a single packet via `depacketize`.
    - Prints decoded packets or prints an error and the raw hex on parse failure.

- `listen_async(self) -> threading.Thread`
  - Runs `listen()` in a separate thread and returns the started thread.

### Script usage (`if __name__ == "__main__":`)
- Demonstrates:
  - Creating a listener, connecting, registering a callback, and running the listener thread.
  - Graceful shutdown on Ctrl+C.

## Development notes / limitations

- The current protocol does not include a packet delimiter, length field, or checksum/CRC; real serial streams typically need one of these to frame packets reliably.
- If packets can arrive back-to-back or split across reads, consider extending the protocol (e.g., add a start byte + length + CRC) and updating `serial_listener.py` to buffer and parse multiple frames.
