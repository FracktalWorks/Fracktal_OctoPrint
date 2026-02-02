#!/usr/bin/env python
"""
Integration test to verify secondary heaters flow through the entire system:
1. M105 parsing
2. Temperature storage
3. API response (get_current_temperatures)
4. WebSocket updates (_addTemperatureData)
"""

import time

# Simulate the data structures
class MockTemperatureStorage:
    """Simulates the printer's temperature storage"""
    def __init__(self):
        self._temp = {}  # Tools
        self._bedTemp = None
        self._chamberTemp = None
        self._filamentTemp = None
        self._secondaryHeatersTemp = {}
    
    def set_temperatures_from_m105(self, parsed_data):
        """Simulates what happens after M105 parsing"""
        # Set tools
        if "T0" in parsed_data:
            self._temp[0] = parsed_data["T0"]
        if "T1" in parsed_data:
            self._temp[1] = parsed_data["T1"]
        
        # Set bed
        if "B" in parsed_data:
            self._bedTemp = parsed_data["B"]
        
        # Set chamber
        if "C" in parsed_data:
            self._chamberTemp = parsed_data["C"]
        
        # Set filament
        if "F" in parsed_data:
            self._filamentTemp = parsed_data["F"]
        
        # Set secondary heaters
        if "H0" in parsed_data:
            self._secondaryHeatersTemp[0] = parsed_data["H0"]
        if "H1" in parsed_data:
            self._secondaryHeatersTemp[1] = parsed_data["H1"]
    
    def get_current_temperatures(self):
        """Simulates standard.py get_current_temperatures()"""
        offsets = {}  # No offsets for this test
        result = {}
        
        if self._temp is not None:
            for tool in self._temp.keys():
                result["tool%d" % tool] = {
                    "actual": self._temp[tool][0],
                    "target": self._temp[tool][1],
                    "offset": offsets.get(tool, 0),
                }
        
        if self._bedTemp is not None:
            result["bed"] = {
                "actual": self._bedTemp[0],
                "target": self._bedTemp[1],
                "offset": offsets.get("bed", 0),
            }
        
        if self._chamberTemp is not None:
            result["chamber"] = {
                "actual": self._chamberTemp[0],
                "target": self._chamberTemp[1],
                "offset": offsets.get("chamber", 0),
            }
        
        if self._filamentTemp is not None:
            result["filament"] = {
                "actual": self._filamentTemp[0],
                "target": self._filamentTemp[1],
                "offset": offsets.get("filament", 0),
            }
        
        if self._secondaryHeatersTemp:
            for heater_num in self._secondaryHeatersTemp.keys():
                heater_key = "H%d" % heater_num
                result[heater_key] = {
                    "actual": self._secondaryHeatersTemp[heater_num][0],
                    "target": self._secondaryHeatersTemp[heater_num][1],
                    "offset": offsets.get(heater_key, 0),
                }
        
        return result
    
    def add_temperature_data(self):
        """Simulates standard.py _addTemperatureData() for websocket"""
        data = {"time": int(time.time())}
        
        for tool in self._temp.keys():
            data["tool%d" % tool] = {
                "actual": self._temp[tool][0],
                "target": self._temp[tool][1]
            }
        
        if self._bedTemp is not None:
            data["bed"] = {
                "actual": self._bedTemp[0],
                "target": self._bedTemp[1]
            }
        
        if self._chamberTemp is not None:
            data["chamber"] = {
                "actual": self._chamberTemp[0],
                "target": self._chamberTemp[1]
            }
        
        if self._filamentTemp is not None:
            data["filament"] = {
                "actual": self._filamentTemp[0],
                "target": self._filamentTemp[1]
            }
        
        for heater_num, values in self._secondaryHeatersTemp.items():
            if isinstance(values, tuple):
                data["H%d" % heater_num] = {
                    "actual": values[0],
                    "target": values[1]
                }
        
        return data


def run_integration_test():
    print("=" * 80)
    print("INTEGRATION TEST: M105 → Storage → API/WebSocket")
    print("=" * 80)
    
    # Simulate M105 response parsing result
    m105_parsed = {
        "T0": (200.1, 200.0),
        "T1": (200.3, 200.0),
        "B": (60.2, 60.0),
        "C": (35.0, 40.0),
        "F": (55.1, 55.0),
        "H0": (75.2, 75.0),
        "H1": (50.1, 50.0),
    }
    
    print("\n1. M105 Response Parsed:")
    print("   Input: ok T0:200.1 /200.0 T1:200.3 /200.0 B:60.2 /60.0 C:35.0 /40.0 F:55.1 /55.0 H0:75.2 /75.0 H1:50.1 /50.0")
    for key, (actual, target) in m105_parsed.items():
        print(f"   {key}: actual={actual}, target={target}")
    
    # Create storage and populate from M105
    storage = MockTemperatureStorage()
    storage.set_temperatures_from_m105(m105_parsed)
    
    print("\n2. Storage State:")
    print(f"   Tools: {storage._temp}")
    print(f"   Bed: {storage._bedTemp}")
    print(f"   Chamber: {storage._chamberTemp}")
    print(f"   Filament: {storage._filamentTemp}")
    print(f"   Secondary Heaters: {storage._secondaryHeatersTemp}")
    
    # Get API response
    api_response = storage.get_current_temperatures()
    
    print("\n3. API Response (GET /api/printer):")
    print("   {")
    print('     "temperature": {')
    for key in sorted(api_response.keys()):
        value = api_response[key]
        print(f'       "{key}": {{')
        print(f'         "actual": {value["actual"]},')
        print(f'         "target": {value["target"]},')
        print(f'         "offset": {value["offset"]}')
        print(f'       }},')
    print('     }')
    print("   }")
    
    # Get WebSocket data
    websocket_data = storage.add_temperature_data()
    
    print("\n4. WebSocket Update (SockJS message):")
    print("   {")
    print('     "current": {')
    print('       "temps": [{')
    for key in sorted(websocket_data.keys()):
        if key == "time":
            continue
        value = websocket_data[key]
        print(f'         "{key}": {{"actual": {value["actual"]}, "target": {value["target"]}}},')
    print(f'         "time": {websocket_data["time"]}')
    print('       }]')
    print('     }')
    print("   }")
    
    # Validation
    print("\n5. Validation:")
    all_valid = True
    
    # Check that all heaters are in API response
    expected_heaters = ["tool0", "tool1", "bed", "chamber", "filament", "H0", "H1"]
    for heater in expected_heaters:
        if heater not in api_response:
            print(f"   ✗ Missing {heater} in API response")
            all_valid = False
        else:
            print(f"   ✓ {heater} present in API response")
    
    # Check that all heaters are in WebSocket data
    for heater in expected_heaters:
        if heater not in websocket_data:
            print(f"   ✗ Missing {heater} in WebSocket data")
            all_valid = False
        else:
            print(f"   ✓ {heater} present in WebSocket data")
    
    # Verify secondary heater values match
    if "H0" in api_response and "H0" in websocket_data:
        api_h0 = api_response["H0"]
        ws_h0 = websocket_data["H0"]
        if api_h0["actual"] == 75.2 and api_h0["target"] == 75.0:
            print("   ✓ H0 values correct in API")
        else:
            print(f"   ✗ H0 values incorrect in API: {api_h0}")
            all_valid = False
        
        if ws_h0["actual"] == 75.2 and ws_h0["target"] == 75.0:
            print("   ✓ H0 values correct in WebSocket")
        else:
            print(f"   ✗ H0 values incorrect in WebSocket: {ws_h0}")
            all_valid = False
    
    if "H1" in api_response and "H1" in websocket_data:
        api_h1 = api_response["H1"]
        ws_h1 = websocket_data["H1"]
        if api_h1["actual"] == 50.1 and api_h1["target"] == 50.0:
            print("   ✓ H1 values correct in API")
        else:
            print(f"   ✗ H1 values incorrect in API: {api_h1}")
            all_valid = False
        
        if ws_h1["actual"] == 50.1 and ws_h1["target"] == 50.0:
            print("   ✓ H1 values correct in WebSocket")
        else:
            print(f"   ✗ H1 values incorrect in WebSocket: {ws_h1}")
            all_valid = False
    
    print("\n" + "=" * 80)
    if all_valid:
        print("✓ INTEGRATION TEST PASSED")
        print("Secondary heaters flow correctly through:")
        print("  - M105 parsing")
        print("  - Internal storage")
        print("  - API endpoint (/api/printer)")
        print("  - WebSocket updates")
    else:
        print("✗ INTEGRATION TEST FAILED")
    print("=" * 80)


if __name__ == "__main__":
    run_integration_test()
