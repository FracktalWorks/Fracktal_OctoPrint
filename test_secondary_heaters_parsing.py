#!/usr/bin/env python
"""
Test script to verify M105 temperature parsing for secondary heaters.

This script simulates the temperature parsing logic to verify that secondary
heaters (H0, H1, etc.) are correctly parsed from M105 responses.
"""

import re

# Regex pattern from OctoPrint comm.py
regex_float_pattern = r"[-+]?[0-9]*\.?[0-9]+"
regex_temp = re.compile(
    r"(?P<tool>B|C|F|T(?P<toolnum>\d*)|H(?P<heaternum>\d*)):\s*(?P<actual>%s)(\s*\/?\s*(?P<target>%s))?"
    % (regex_float_pattern, regex_float_pattern)
)

def parse_m105_line(line):
    """Simulate the M105 parsing logic."""
    result = {}
    for match in re.finditer(regex_temp, line):
        values = match.groupdict()
        tool = values["tool"]
        
        try:
            actual = float(values["actual"])
            target = None
            if values.get("target"):
                target = float(values["target"])
            
            result[tool] = (actual, target)
        except (ValueError, TypeError):
            pass
    
    return result

# Test cases
test_cases = [
    {
        "name": "Standard M105 with secondary heaters",
        "line": "ok T:25.0 /0.0 B:25.0 /0.0 T0:25.0 /0.0 T1:25.0 /0.0 H0:25.0 /0.0 H1:25.0 /0.0",
        "expected": {
            "T": (25.0, 0.0),
            "B": (25.0, 0.0),
            "T0": (25.0, 0.0),
            "T1": (25.0, 0.0),
            "H0": (25.0, 0.0),
            "H1": (25.0, 0.0),
        }
    },
    {
        "name": "M105 with active heating",
        "line": "ok T:180.5 /200.0 B:60.3 /60.0 H0:75.2 /80.0 H1:45.0 /50.0",
        "expected": {
            "T": (180.5, 200.0),
            "B": (60.3, 60.0),
            "H0": (75.2, 80.0),
            "H1": (45.0, 50.0),
        }
    },
    {
        "name": "M105 with all heater types",
        "line": "ok T:200.0 /200.0 B:60.0 /60.0 C:30.0 /40.0 F:50.0 /55.0 H0:70.0 /75.0 H1:80.0 /85.0",
        "expected": {
            "T": (200.0, 200.0),
            "B": (60.0, 60.0),
            "C": (30.0, 40.0),
            "F": (50.0, 55.0),
            "H0": (70.0, 75.0),
            "H1": (80.0, 85.0),
        }
    },
    {
        "name": "M105 with 4 secondary heaters",
        "line": "ok T0:200.0 /200.0 T1:200.0 /200.0 T2:200.0 /200.0 T3:200.0 /200.0 B:60.0 /60.0 H0:70.0 /75.0 H1:80.0 /85.0 H2:90.0 /95.0 H3:100.0 /105.0",
        "expected": {
            "T0": (200.0, 200.0),
            "T1": (200.0, 200.0),
            "T2": (200.0, 200.0),
            "T3": (200.0, 200.0),
            "B": (60.0, 60.0),
            "H0": (70.0, 75.0),
            "H1": (80.0, 85.0),
            "H2": (90.0, 95.0),
            "H3": (100.0, 105.0),
        }
    },
    {
        "name": "M105 with no targets",
        "line": "ok T:25.0 B:25.0 H0:25.0 H1:25.0",
        "expected": {
            "T": (25.0, None),
            "B": (25.0, None),
            "H0": (25.0, None),
            "H1": (25.0, None),
        }
    },
]

print("=" * 80)
print("TESTING M105 TEMPERATURE PARSING FOR SECONDARY HEATERS")
print("=" * 80)

all_passed = True
for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Input: {test['line']}")
    
    result = parse_m105_line(test['line'])
    
    # Check if result matches expected
    passed = result == test['expected']
    
    if passed:
        print("✓ PASSED")
    else:
        print("✗ FAILED")
        print(f"  Expected: {test['expected']}")
        print(f"  Got:      {result}")
        all_passed = False
    
    # Show parsed values
    print("  Parsed values:")
    for key, (actual, target) in sorted(result.items()):
        target_str = f"{target}" if target is not None else "None"
        print(f"    {key}: actual={actual}, target={target_str}")

print("\n" + "=" * 80)
if all_passed:
    print("✓ ALL TESTS PASSED")
else:
    print("✗ SOME TESTS FAILED")
print("=" * 80)
