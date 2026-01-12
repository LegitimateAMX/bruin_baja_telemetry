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


# File: `pc_depacketizer.py`

# `DataDepacketizer` Class

A class to read, parse (depacketize), and store data packets from CSV files. Each packet is expected to be in the format:

```
[ address(1 byte) | type_code(1 byte) | num_vars(1 byte) | payload... ]
```

* Supports reading multiple CSV files from a directory or a single CSV file.
* Supports direct parsing of bytes. 
* Can write parsed data to a CSV file (will create parent directories if needed).
* Stores all parsed packets internally in a list.
* Can output stored data as a list. 
* Data is stored in the format: address, value1, value2, ...
* Stores source path. 
* Stores CSV to write to path. 

---

## Class Methods

### `__init__(self, source_path=None, csv_file=None)`

Initialize the object.

**Parameters:**

* `source_path` (str or Path, optional) – Directory or CSV file to read from.
* `csv_file` (str or Path, optional) – CSV file to write output to.

**Notes:**

* Paths can be relative or absolute.
* Internal list `self.data` is initialized empty.

---

### `depacketize(self, data: bytes)`

Parse a single packet into address and payload values.

**Parameters:**

* `data` (bytes) – A byte array representing one packet.

**Returns:**

* List: `[address, value1, value2, ...]`

**Raises:**

* `ValueError` if packet is too short or payload size doesn't match header.

**Behavior:**

* Appends the parsed packet to `self.data`.

---

### `readFromCSVs(self, source_path=None)`

Read CSV files and depacketize the rows.

**Parameters:**

* `source_path` (str or Path, optional) – Overrides the saved `source_path` if provided.

**Behavior:**

* Reads all `.csv` files in the directory if a folder is provided.
* Reads the single file if a file path is provided.
* Converts CSV string hex values (e.g., `"0A"`) to bytes before depacketizing.
* Appends each packet to `self.data`.

**Raises:**

* `ValueError` if no path is provided.
* `FileNotFoundError` if the path does not exist.

---

### `writeToCSV(self, csv_file=None)`

Write parsed data (`self.data`) to a CSV file.

**Parameters:**

* `csv_file` (str or Path, optional) – CSV file to write to, overrides saved file.

**Behavior:**

* Creates parent directories if they don’t exist.
* Appends all rows in `self.data` to the CSV file.

**Raises:**

* `ValueError` if no CSV file is specified.

---

### `outputList(self)`

Return all parsed packets as a list.

**Returns:**

* `List[List]` – Each inner list is `[address, value1, value2, ...]`.

---

### `getSource(self)`

Return the currently set source path.

**Returns:**

* `Path` – Saved source path.

---

### `getCSV(self)`

Return the currently set CSV file path.

**Returns:**

* `Path` – Saved CSV file path.

---

### `clearData(self)`

Clear the internal data list.

**Behavior:**

* Empties `self.data` to start fresh.

---

## Example Usage

```python
# Initialize with a directory of CSVs and an output CSV
dep = DataDepacketizer(source_path="C:/Baja/test_data", csv_file="C:/Baja/outputs/output.csv")

# Read and depacketize CSV files
dep.readFromCSVs()

# Check parsed data
print(dep.outputList())

# Write parsed data to CSV
dep.writeToCSV()

# Clear data
dep.clearData()
print(dep.outputList())  # Should print []
```

---
## Script usage (`if __name__ == "__main__":`)
*Runs simple test cases for the class functions 


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
