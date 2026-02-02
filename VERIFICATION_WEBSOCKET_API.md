# Secondary Heaters: Complete Data Flow Verification

## ✅ CONFIRMED: Full Integration Working

The secondary heaters implementation correctly flows temperature data through all layers of OctoPrint:

```
Firmware (M105) → Parsing → Storage → API → WebSocket → UI
```

---

## Data Flow Step-by-Step

### 1. Firmware Sends M105 Response
```
ok T:200.1 /200.0 T0:200.1 /200.0 T1:200.3 /200.0 B:60.2 /60.0 C:35.0 /40.0 F:55.1 /55.0 H0:75.2 /75.0 H1:50.1 /50.0
```

**Contains:**
- Tools: T, T0, T1
- Bed: B
- Chamber: C
- Filament: F
- **Secondary Heaters: H0, H1** ✓

---

### 2. Regex Parsing (comm.py)

**Pattern:**
```python
regex_temp = re.compile(
    r"(?P<tool>B|C|F|T(?P<toolnum>\d*)|H(?P<heaternum>\d*)):\s*(?P<actual>%s)(\s*\/?\s*(?P<target>%s))?"
    % (regex_float_pattern, regex_float_pattern)
)
```

**Extracts:**
```python
{
    "T0": (200.1, 200.0),
    "T1": (200.3, 200.0),
    "B": (60.2, 60.0),
    "C": (35.0, 40.0),
    "F": (55.1, 55.0),
    "H0": (75.2, 75.0),  # ✓ Parsed correctly
    "H1": (50.1, 50.0),  # ✓ Parsed correctly
}
```

---

### 3. Temperature Processing (comm.py `_processTemperatures`)

**Code:**
```python
# secondary heaters (H0, H1, etc.)
if self._printerProfileManager.get_current_or_default().get("hasSecondaryHeaters", False):
    extruder_count = self._printerProfileManager.get_current_or_default()["extruder"]["count"]
    for n in range(extruder_count):
        heater_key = "H%d" % n
        if heater_key in parsedTemps:
            actual, target = parsedTemps[heater_key]
            del parsedTemps[heater_key]
            self.last_temperature.set_secondary_heater(n, actual=actual, target=target)
```

**Result:**
```python
TemperatureRecord:
  _secondary_heaters = {
    0: (75.2, 75.0),  # ✓ Stored
    1: (50.1, 50.0),  # ✓ Stored
  }
```

---

### 4. Temperature Update Callback (standard.py)

**Code:**
```python
def on_comm_temperature_update(self, temp, bedTemp, chamberTemp, filamentTemp, secondaryHeaters, customTemp):
    self._addTemperatureData(
        tools=temp,
        bed=bedTemp,
        chamber=chamberTemp,
        filament=filamentTemp,
        secondary_heaters=secondaryHeaters,  # ✓ Passed through
        custom=customTemp
    )
```

---

### 5. Add Temperature Data (standard.py `_addTemperatureData`)

**Code:**
```python
def _addTemperatureData(self, tools=None, bed=None, chamber=None, filament=None, secondary_heaters=None, custom=None):
    # ... (initialize defaults)
    
    data = {"time": int(time.time())}
    
    # Add tools, bed, chamber, filament...
    
    # Add secondary heaters ✓
    for heater_num, values in secondary_heaters.items():
        if isinstance(values, tuple):
            data["H%d" % heater_num] = self._dict(actual=values[0], target=values[1])
    
    # Store internally
    self._secondaryHeatersTemp = secondary_heaters  # ✓ Stored
    
    # Send to websocket
    self._stateMonitor.add_temperature(self._dict(**data))  # ✓ Sent
```

**WebSocket Data:**
```python
{
    "tool0": {"actual": 200.1, "target": 200.0},
    "tool1": {"actual": 200.3, "target": 200.0},
    "bed": {"actual": 60.2, "target": 60.0},
    "chamber": {"actual": 35.0, "target": 40.0},
    "filament": {"actual": 55.1, "target": 55.0},
    "H0": {"actual": 75.2, "target": 75.0},  # ✓ Included
    "H1": {"actual": 50.1, "target": 50.0},  # ✓ Included
    "time": 1769866024
}
```

---

### 6. API Response (standard.py `get_current_temperatures`)

**Code:**
```python
def get_current_temperatures(self, *args, **kwargs):
    # ... (process offsets, tools, bed, chamber, filament)
    
    # Add secondary heaters ✓
    if self._secondaryHeatersTemp:
        for heater_num in self._secondaryHeatersTemp.keys():
            heater_key = "H%d" % heater_num
            result[heater_key] = {
                "actual": self._secondaryHeatersTemp[heater_num][0],
                "target": self._secondaryHeatersTemp[heater_num][1],
                "offset": offsets[heater_key] if heater_key in offsets else 0,
            }
    
    return result
```

**API Response (GET /api/printer):**
```json
{
  "temperature": {
    "tool0": {"actual": 200.1, "target": 200.0, "offset": 0},
    "tool1": {"actual": 200.3, "target": 200.0, "offset": 0},
    "bed": {"actual": 60.2, "target": 60.0, "offset": 0},
    "chamber": {"actual": 35.0, "target": 40.0, "offset": 0},
    "filament": {"actual": 55.1, "target": 55.0, "offset": 0},
    "H0": {"actual": 75.2, "target": 75.0, "offset": 0},
    "H1": {"actual": 50.1, "target": 50.0, "offset": 0}
  },
  "state": { ... }
}
```

✓ **Secondary heaters H0 and H1 are included in API response**

---

### 7. WebSocket Push (StateMonitor → callbacks)

**Flow:**
```
_addTemperatureData()
  → self._stateMonitor.add_temperature(data)
    → _sendAddTemperatureCallbacks(data)
      → callback.on_printer_add_temperature(data)
        → SockJS sends to connected clients
```

**WebSocket Message:**
```json
{
  "current": {
    "temps": [{
      "tool0": {"actual": 200.1, "target": 200.0},
      "tool1": {"actual": 200.3, "target": 200.0},
      "bed": {"actual": 60.2, "target": 60.0},
      "chamber": {"actual": 35.0, "target": 40.0},
      "filament": {"actual": 55.1, "target": 55.0},
      "H0": {"actual": 75.2, "target": 75.0},
      "H1": {"actual": 50.1, "target": 50.0},
      "time": 1769866024
    }],
    "state": { ... }
  }
}
```

✓ **Secondary heaters H0 and H1 are included in WebSocket updates**

---

### 8. UI Display (temperature.js viewmodel)

**Code:**
```javascript
// Secondary heaters are in the observable array
self.secondaryHeaters = ko.observableArray([]);

// Process temperature updates
var secondaryHeaters = self.secondaryHeaters();
for (var i = 0; i < secondaryHeaters.length; i++) {
    var key = "H" + i;
    if (lastData.hasOwnProperty(key)) {
        secondaryHeaters[i]["actual"](lastData[key].actual);  // ✓ Updates UI
        secondaryHeaters[i]["target"](lastData[key].target);  // ✓ Updates UI
    }
}
```

**Template (temperature.jinja2):**
```html
<!-- Secondary heaters rows -->
<!-- ko foreach: secondaryHeaters -->
<tr data-bind="template: { name: 'temprow-template' }, visible: $root.hasSecondaryHeaters"></tr>
<!-- /ko -->
```

✓ **Secondary heaters display in UI temperature table**

---

## Verification Results

### ✅ Integration Test Results

**Test Script:** `test_secondary_heaters_integration.py`

```
✓ tool0 present in API response
✓ tool1 present in API response
✓ bed present in API response
✓ chamber present in API response
✓ filament present in API response
✓ H0 present in API response          ← CONFIRMED
✓ H1 present in API response          ← CONFIRMED
✓ tool0 present in WebSocket data
✓ tool1 present in WebSocket data
✓ bed present in WebSocket data
✓ chamber present in WebSocket data
✓ filament present in WebSocket data
✓ H0 present in WebSocket data        ← CONFIRMED
✓ H1 present in WebSocket data        ← CONFIRMED
✓ H0 values correct in API            ← CONFIRMED
✓ H0 values correct in WebSocket      ← CONFIRMED
✓ H1 values correct in API            ← CONFIRMED
✓ H1 values correct in WebSocket      ← CONFIRMED

INTEGRATION TEST PASSED
```

---

## Key Implementation Points

### 1. Storage Layer ✅
```python
# standard.py
self._secondaryHeatersTemp = {}  # Stores: {0: (actual, target), 1: (actual, target)}
```

### 2. Data Format ✅
Secondary heaters use the same format as other heaters:
```python
"H0": {"actual": 75.2, "target": 75.0, "offset": 0}
"H1": {"actual": 50.1, "target": 50.0, "offset": 0}
```

### 3. API Endpoints ✅
- `GET /api/printer` - Returns all temperatures including H0, H1
- `GET /api/printer/heater/<num>` - Returns specific secondary heater
- `POST /api/printer/heater/<num>` - Controls specific secondary heater

### 4. WebSocket Updates ✅
Secondary heaters are automatically included in all temperature updates sent via SockJS:
- Same structure as other heaters
- Same update frequency
- No special handling required by clients

### 5. UI Integration ✅
- Observable array: `self.secondaryHeaters()`
- Auto-creates entries based on extruder count
- Uses same temperature row template
- Shows when `hasSecondaryHeaters` is enabled

---

## Summary

### ✅ COMPLETE IMPLEMENTATION VERIFIED

**Both API and WebSocket correctly return secondary heater information:**

1. **M105 Parsing** - H0, H1 are parsed from firmware responses
2. **Internal Storage** - Stored in `_secondaryHeatersTemp` dict
3. **API Response** - Included in `/api/printer` with format `{"H0": {...}, "H1": {...}}`
4. **WebSocket Updates** - Automatically pushed to all connected clients
5. **UI Display** - Rendered in temperature table and graphs

**The implementation follows the exact same pattern as:**
- Tools (T0, T1) - Uses dict storage
- Bed (B) - Included in API/WebSocket
- Chamber (C) - Included in API/WebSocket
- Filament (F) - Included in API/WebSocket

**No additional configuration needed** - secondary heaters automatically flow through all data channels when:
- `hasSecondaryHeaters` is enabled in printer profile
- Firmware sends H0, H1, etc. in M105 responses
