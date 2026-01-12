import struct
import csv
from pathlib import Path

class DataDepacketizer:
    def __init__(self, source_path = None, csv_file=None):
        self.csv_file = Path(csv_file) if csv_file else None
        self.source_path = Path(source_path) if source_path else None
        self.data = []

    def depacketize(self, data: bytes):
        """
        Expected packet:
        [ address(1) | type_code(1) | num_vars(1) | payload... ]
        """
        if len(data) < 3:
            raise ValueError("Packet too short")

        address = data[0]
        type_code = chr(data[1])
        num_vars = data[2]

        fmt = "<" + str(num_vars) + type_code
        payload = data[3:]

        if len(payload) != struct.calcsize(fmt):
            raise ValueError("Payload size mismatch")

        values = struct.unpack(fmt, payload)
        self.data.append([address] + list(values))
        return [address] + list(values)

    def readFromCSVs(self, source_path = None):
        # Use saved source path if none provided
        path_to_use = source_path or self.source_path
        if path_to_use is None:
            raise ValueError("No source path provided")
        source = Path(path_to_use)
        if not source.exists():
            raise FileNotFoundError(f"Path does not exist: {source}")
        self.source_path = source

        #files to read
        files_to_read = []
        if source.is_dir():
            files_to_read = list(source.glob("*.csv"))
        elif source.is_file():
            files_to_read = [source]

        #reads through file list
        for csv_f in files_to_read:
            with open(csv_f, newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    # Convert CSV string values to ints
                    try:
                        byte_values = [int(x, 16) for x in row]  # hex to int
                    except ValueError:
                        raise ValueError(f"Invalid byte value in {csv_f}: {row}")
                    # Make bytes object
                    packet = bytes(byte_values)
                    # Pass to depacketize
                    self.depacketize(packet)
        
    def writeToCSV(self, csv_file = None):
        #path checking and replacement
        target_file = csv_file or self.csv_file
        if target_file is None:
            raise ValueError("No CSV file specified")
        csv_path = Path(target_file)

        # Make sure parent directories exist
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_file = csv_path

        #writing to csv
        with open(csv_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            for d in self.data:
                writer.writerow(d)
        
    def outputList(self):
        return self.data
    
    def getSource(self):
        return self.source_path
    
    def getCSV(self):
        return self.csv_file
    
    def clearData(self):
        self.data = []

def test_depacketize():
    # Create an instance (CSV and source_path not needed for this test)
    dp = DataDepacketizer()

    # --- TEST CASE 1: single float value ---
    address = 1
    type_code = 'f'
    num_vars = 1
    payload = struct.pack('<f', 3.14)
    packet = bytes([address]) + bytes(type_code, 'ascii') + bytes([num_vars]) + payload

    result = dp.depacketize(packet)
    assert len(result) == 2, "Test 1 failed: length mismatch"
    assert result[0] == 1, "Test 1 failed: wrong address"
    assert abs(result[1] - 3.14) < 1e-6, "Test 1 failed: wrong float value"

    # --- TEST CASE 2: multiple integers ---
    address = 5
    type_code = 'i'
    num_vars = 3
    payload = struct.pack('<3i', 10, 20, 30)
    packet = bytes([address]) + bytes(type_code, 'ascii') + bytes([num_vars]) + payload

    result = dp.depacketize(packet)
    assert result == [5, 10, 20, 30], "Test 2 failed"

    # --- TEST CASE 3: packet too short ---
    short_packet = bytes([1, ord('f')])
    try:
        dp.depacketize(short_packet)
        assert False, "Test 3 failed: expected ValueError for short packet"
    except ValueError:
        pass  # expected

    # --- TEST CASE 4: payload size mismatch ---
    address = 2
    type_code = 'f'
    num_vars = 2
    payload = struct.pack('<f', 1.23)  # only 1 float instead of 2
    packet = bytes([address]) + bytes(type_code, 'ascii') + bytes([num_vars]) + payload

    try:
        dp.depacketize(packet)
        assert False, "Test 4 failed: expected ValueError for payload size mismatch"
    except ValueError:
        pass  # expected

    # --- TEST CASE 5: internal data list ---
    # It should contain results from Test 1 and Test 2
    expected_data = [
        [1, 3.14],
        [5, 10, 20, 30]
    ]
    # Only compare first two entries since Tests 3 & 4 failed packets
    for i, expected in enumerate(expected_data):
        for j, val in enumerate(expected):
            if isinstance(val, float):
                assert abs(dp.data[i][j] - val) < 1e-6, f"Test 5 failed at data[{i}][{j}]"
            else:
                assert dp.data[i][j] == val, f"Test 5 failed at data[{i}][{j}]"

    print("All depacketize tests passed!")

def test_all():
    test_dir = Path("test_dir")
    test_dir.mkdir(exist_ok=True)

    test1_file = test_dir / "test1.csv"
    test2_file = test_dir / "test2.csv"
    output_file = test_dir / "outputs"/"output.csv"

    # Packets for test1.csv: [address, type_code, num_vars, payload...]
    packets1 = [
        [1, ord('f'), 2] + list(struct.pack("<ff", 3.14, 2.71)),
        [2, ord('i'), 3] + list(struct.pack("<iii", 10, 20, 30)),
    ]

    # Write packets1 as hex strings
    with open(test1_file, "w", newline="") as f:
        writer = csv.writer(f)
        for row in packets1:
            writer.writerow([f"{b:02x}" for b in row])

    # Packets for test2.csv: different data
    packets2 = [
        [3, ord('f'), 1] + list(struct.pack("<f", 1.23)),
        [4, ord('i'), 2] + list(struct.pack("<ii", 100, 200)),
    ]

    # Write packets2 as hex strings
    with open(test2_file, "w", newline="") as f:
        writer = csv.writer(f)
        for row in packets2:
            writer.writerow([f"{b:02x}" for b in row])

    dp = DataDepacketizer(csv_file=output_file)
    dp.readFromCSVs(test1_file)  # read test1.csv
    dp.writeToCSV()               # write to output.csv
    print(dp.outputList())
    dp.clearData()
    dp.readFromCSVs("test_dir")
    dp.writeToCSV("test_dir/outputs/new_output.csv")
    # shutil.rmtree(test_dir)

if __name__ =="__main__":
    test_depacketize()
    test_all()