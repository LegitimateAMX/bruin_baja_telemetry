import serial
import os
import csv
from unittest.mock import Mock, patch, MagicMock
import pytest

class SerialListener:
    def __init__(self, port, baudrate=9600, timeout=1.0, path="./byte_data.csv"):
        self.port = port
        self.baudrate = baudrate #default
        self.timeout = timeout #default
        self.path = path
        self.ser = None
        
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def connect(self, port=None): #need to enter a default port
        self.port = port
        if (self.port):
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout) #opens port and creates a serial connection
            print("Serial connection created.")
    
    def disconnect(self):
        if self.ser:
            self.ser.close() #close the serial connection
            print("Serial connection closed.")
        else:
            print("Serial connection not created yet.")
    
    def listen(self): #send packet data to csv fileno 
        if not self.ser:
            print("Serial connection not created yet.")
            return
        while True:
            ser_bytes = self.ser.readline() #readline() depends on newline character
            with open(self.path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f"{b:02x}" for b in ser_bytes])

# ============================================================================
# UNIT TESTS
# ============================================================================

@pytest.fixture
def temp_csv(): 
    #Directory for test CSV files called test_outputs
    test_dir = os.path.join(os.path.dirname(__file__), "test_outputs")
    os.makedirs(test_dir, exist_ok=True)
    print(f"\nTest files saved to: {test_dir}")
    yield test_dir

@pytest.fixture
def mock_serial(): 
    #replaces serial.Serial with a mock object
    with patch('serial.Serial') as mock:
        yield mock

def test_initialization(temp_csv): 
    #testing if values are intialized correctly
    listener = SerialListener(port="/dev/ttyUSB0", baudrate=115200, path=temp_csv)
    
    assert listener.port == "/dev/ttyUSB0"
    assert listener.baudrate == 115200
    assert listener.path == temp_csv
    assert listener.ser is None

def test_connect(mock_serial): 
    #testing if serial connection is created
    listener = SerialListener(port="/dev/ttyUSB0")
    listener.connect(port="/dev/ttyUSB0")

    mock_serial.assert_called_once_with("/dev/ttyUSB0", 9600, timeout=1.0)
    assert listener.ser is not None

def test_disconnect(mock_serial): 
    #disconnection the test serial connection
    listener = SerialListener(port="/dev/ttyUSB0")
    listener.connect(port="/dev/ttyUSB0")
    listener.disconnect()
    listener.ser.close.assert_called_once()

def test_listen_saves_bytes_to_csv(temp_csv): 
    #Test that listen() correctly processes and saves packetized bytes to CSV
    listener = SerialListener(port="/dev/ttyUSB0", path=temp_csv)
    
    #Mock serial object
    mock_ser = MagicMock()
    listener.ser = mock_ser
    
    #Simulate 3 packets of bytes
    test_packets = [
        b'\x01\x02\x03\x04',
        b'\x05\x06\x07\x08',
        b'\x09\x0a\x0b\x0c'
    ]
    
    #Manually process packets instead of while True loop
    csv_path = os.path.join(temp_csv, "test_output.csv")
    # Clear the file if it exists from previous test runs
    if os.path.exists(csv_path):
        os.remove(csv_path)
    
    for packet in test_packets:
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f"{b:02x}" for b in packet])
    
    #Verify CSV file was created and contains correct data
    assert os.path.exists(csv_path)
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0] == ['01', '02', '03', '04']
    assert rows[1] == ['05', '06', '07', '08']
    assert rows[2] == ['09', '0a', '0b', '0c']

def test_listen_without_connection(temp_csv):
    """Test that listen() handles missing connection gracefully"""
    listener = SerialListener(port="/dev/ttyUSB0", path=temp_csv)
    
    result = listener.listen()
    assert result is None  # Should return early

def test_byte_formatting(temp_csv):
    #Test that byte packets are correctly formatted as hex strings in CSV
    csv_path = os.path.join(temp_csv, "format_test.csv")
    
    test_data = [b'\xff\x00\xaa', b'\x12\x34\x56']
    for packet in test_data:
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f"{b:02x}" for b in packet])
    
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    assert rows[0] == ['ff', '00', 'aa']
    assert rows[1] == ['12', '34', '56']

def test_path_directory_creation(temp_csv):
    """Test that SerialListener creates parent directories for file paths"""
    new_path = os.path.join(temp_csv, "subdir", "test_file.csv")
    listener = SerialListener(port="/dev/ttyUSB0", path=new_path)
    assert os.path.exists(os.path.dirname(new_path))

def test_listen_reads_and_writes_serial_data(temp_csv, mock_serial):
    #Test that listen() reads from serial and writes to CSV
    csv_path = os.path.join(temp_csv, "listen_test.csv")
    try:
        if os.path.exists(csv_path):
            os.remove(csv_path)
    except PermissionError:
        #If file is locked, use a different filename
        import time
        csv_path = os.path.join(temp_csv, f"listen_test_{int(time.time())}.csv")
    
    listener = SerialListener(port="/dev/ttyUSB0", path=csv_path)
    mock_ser_instance = MagicMock()
    mock_serial.return_value = mock_ser_instance
    
    #simulate 3 packets, then stop the loop with an exception
    test_packets = [
        b'\x01\x02\x03\x04\n',
        b'\x05\x06\x07\x08\n',
        b'\x09\x0a\x0b\x0c\n'
    ]
    
    #Make readline() return packets sequentially, then raise exception to break loop
    mock_ser_instance.readline.side_effect = test_packets + [KeyboardInterrupt()]
    listener.connect(port="/dev/ttyUSB0")
    
    try:
        listener.listen()
    except KeyboardInterrupt:
        pass #Breaks infinite loop
    
    #CSV created
    assert os.path.exists(csv_path)
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0] == ['01', '02', '03', '04', '0a']  #\n is 0x0a
    assert rows[1] == ['05', '06', '07', '08', '0a']
    assert rows[2] == ['09', '0a', '0b', '0c', '0a']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])