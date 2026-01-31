# Secondary Heaters Implementation Review

## Overview
Secondary heaters (H0, H1, H2, etc.) are additional heating elements that can be controlled independently, one per extruder. They are parsed from M105 temperature responses and controlled via M104 commands.

## M105 Temperature Reading

### Example M105 Output
```
ok T:25.0 /0.0 B:25.0 /0.0 T0:25.0 /0.0 T1:25.0 /0.0 H0:25.0 /0.0 H1:25.0 /0.0
```

### Parsing Logic

The temperature regex pattern in comm.py:
```python
regex_temp = re.compile(
    r"(?P<tool>B|C|F|T(?P<toolnum>\d*)|H(?P<heaternum>\d*)):\s*(?P<actual>%s)(\s*\/?\s*(?P<target>%s))?"
    % (regex_float_pattern, regex_float_pattern)
)
```

This pattern matches:
- **B**: Bed temperature
- **C**: Chamber temperature  
- **F**: Filament temperature
- **T** or **T0-T9**: Tool/extruder temperatures
- **H0-H9**: Secondary heater temperatures

### Processing Flow

1. **Regex Parsing**: `parse_temperature_line()` extracts all temperature values from M105 response
2. **Tool Processing**: Tools (T0, T1, etc.) are processed first
3. **Special Heaters**: Bed (B), Chamber (C), Filament (F) are processed next
4. **Secondary Heaters**: H0, H1, etc. are processed if `hasSecondaryHeaters` is enabled
5. **Custom Heaters**: Any remaining unrecognized heaters go to custom

### Code Location: comm.py `_processTemperatures()` method

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

**Key Points:**
- Only processes secondary heaters if `hasSecondaryHeaters` is True in printer profile
- Number of secondary heaters matches extruder count
- Each heater is identified as H0, H1, H2, etc.
- Values are removed from `parsedTemps` after processing (prevents duplicate processing)

## Temperature Control Commands

### M104 Command Format
Secondary heaters use the M104 command with H parameter:
```
M104 H0 S50   # Set H0 to 50°C
M104 H1 S75   # Set H1 to 75°C
M104 H0 S0    # Turn off H0
```

### Code Location: standard.py `set_temperature()` method

```python
elif heater.startswith("H"):
    heaterNum = int(heater[1:])
    self.commands("M104 H{} S{}".format(heaterNum, value), tags=tags)
```

## API Endpoints

### 1. Set Secondary Heater Target Temperature

**Endpoint:** `POST /api/printer/heater/<heater_num>`

**Parameters:**
- `heater_num` (int, in URL): The heater number (0, 1, 2, etc.)

**Request Body:**
```json
{
  "command": "target",
  "target": 75
}
```

**Example:**
```bash
# Set H0 to 75°C
curl -X POST http://octopi.local/api/printer/heater/0 \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"target","target":75}'

# Set H1 to 50°C
curl -X POST http://octopi.local/api/printer/heater/1 \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"target","target":50}'

# Turn off H0
curl -X POST http://octopi.local/api/printer/heater/0 \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"target","target":0}'
```

**Response:** `204 No Content` on success

**Error Responses:**
- `400 Bad Request`: Invalid heater number or target value
- `403 Forbidden`: Insufficient permissions
- `409 Conflict`: Printer not operational or secondary heaters not enabled

---

### 2. Set Secondary Heater Temperature Offset

**Endpoint:** `POST /api/printer/heater/<heater_num>`

**Parameters:**
- `heater_num` (int, in URL): The heater number (0, 1, 2, etc.)

**Request Body:**
```json
{
  "command": "offset",
  "offset": 5
}
```

**Offset Range:** -50 to +50°C

**Example:**
```bash
# Set H0 offset to +5°C
curl -X POST http://octopi.local/api/printer/heater/0 \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"offset","offset":5}'

# Set H1 offset to -3°C
curl -X POST http://octopi.local/api/printer/heater/1 \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"offset","offset":-3}'
```

**Response:** `204 No Content` on success

---

### 3. Get Secondary Heater State

**Endpoint:** `GET /api/printer/heater/<heater_num>`

**Parameters:**
- `heater_num` (int, in URL): The heater number (0, 1, 2, etc.)

**Example:**
```bash
# Get H0 state
curl -X GET http://octopi.local/api/printer/heater/0 \
  -H "X-Api-Key: YOUR_API_KEY"

# Get H1 state  
curl -X GET http://octopi.local/api/printer/heater/1 \
  -H "X-Api-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "temperature": {
    "H0": {
      "actual": 75.2,
      "target": 75.0,
      "offset": 0
    }
  }
}
```

---

### 4. Get All Temperatures (includes secondary heaters)

**Endpoint:** `GET /api/printer`

**Example:**
```bash
curl -X GET http://octopi.local/api/printer \
  -H "X-Api-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "temperature": {
    "tool0": {
      "actual": 200.1,
      "target": 200.0,
      "offset": 0
    },
    "tool1": {
      "actual": 200.3,
      "target": 200.0,
      "offset": 0
    },
    "bed": {
      "actual": 60.0,
      "target": 60.0,
      "offset": 0
    },
    "H0": {
      "actual": 75.2,
      "target": 75.0,
      "offset": 0
    },
    "H1": {
      "actual": 50.1,
      "target": 50.0,
      "offset": 0
    }
  },
  "state": {
    "text": "Printing",
    "flags": {
      "operational": true,
      "printing": true,
      "paused": false,
      "ready": false
    }
  }
}
```

## JavaScript Client API

### Methods

```javascript
// Set secondary heater target temperature
OctoPrint.printer.setSecondaryHeaterTargetTemperature(heater, target)

// Set secondary heater temperature offset
OctoPrint.printer.setSecondaryHeaterTemperatureOffset(heater, offset)

// Get secondary heater state
OctoPrint.printer.getSecondaryHeaterState(heater)
```

### Example Usage

```javascript
// Set H0 to 75°C
OctoPrint.printer.setSecondaryHeaterTargetTemperature(0, 75);

// Set H1 to 50°C
OctoPrint.printer.setSecondaryHeaterTargetTemperature(1, 50);

// Set H0 offset to +5°C
OctoPrint.printer.setSecondaryHeaterTemperatureOffset(0, 5);

// Get H0 state
OctoPrint.printer.getSecondaryHeaterState(0).done(function(response) {
    console.log("H0 temperature:", response.temperature.H0);
});
```

## WebSocket Updates

Secondary heaters are included in the regular temperature updates via websocket:

```json
{
  "current": {
    "temps": [{
      "tool0": {"actual": 200.0, "target": 200.0},
      "tool1": {"actual": 200.0, "target": 200.0},
      "bed": {"actual": 60.0, "target": 60.0},
      "H0": {"actual": 75.0, "target": 75.0},
      "H1": {"actual": 50.0, "target": 50.0},
      "time": 1234567890
    }],
    "state": {
      "text": "Printing",
      "flags": {
        "operational": true,
        "printing": true
      }
    }
  }
}
```

## Printer Profile Configuration

Enable secondary heaters in the printer profile:

### Via UI
1. Go to Settings → Printer Profiles
2. Edit your printer profile
3. Check "Has Secondary Heaters" checkbox
4. Set the extruder count (secondary heaters will match this count)

### Via API/JSON
```json
{
  "id": "my_printer",
  "name": "My Printer",
  "extruder": {
    "count": 2
  },
  "hasSecondaryHeaters": true
}
```

## Implementation Comparison with Other Heaters

### Bed Heater (for comparison)
- **M105 Format:** `B:60.0 /60.0`
- **Control Command:** `M140 S60`
- **API Endpoint:** `/api/printer/bed`
- **Storage:** Single tuple `_bedTemp = (actual, target)`
- **Profile Toggle:** `heatedBed`

### Chamber Heater (for comparison)
- **M105 Format:** `C:30.0 /40.0`
- **Control Command:** `M141 S40`
- **API Endpoint:** `/api/printer/chamber`
- **Storage:** Single tuple `_chamberTemp = (actual, target)`
- **Profile Toggle:** `heatedChamber`

### Filament Heater (for comparison)
- **M105 Format:** `F:50.0 /55.0`
- **Control Command:** `M142 S55`
- **API Endpoint:** `/api/printer/filament`
- **Storage:** Single tuple `_filamentTemp = (actual, target)`
- **Profile Toggle:** `heatedFilament`

### Secondary Heaters (current implementation)
- **M105 Format:** `H0:75.0 /80.0 H1:50.0 /55.0`
- **Control Command:** `M104 H0 S80` or `M104 H1 S55`
- **API Endpoint:** `/api/printer/heater/<num>`
- **Storage:** Dictionary `_secondaryHeatersTemp = {0: (actual, target), 1: (actual, target)}`
- **Profile Toggle:** `hasSecondaryHeaters`

### Key Differences

**Secondary heaters are unique because:**
1. **Multiple heaters** - Dict storage instead of single tuple (like tools)
2. **Count matches extruders** - Number is determined by extruder count
3. **Numbered identifiers** - H0, H1, H2 (like T0, T1, T2)
4. **Shared command** - Uses M104 with H parameter (same as tools use M104 with T parameter)
5. **No temperature profiles** - Unlike bed/chamber/filament, secondary heaters don't have profile presets

**Similarities with other heaters:**
1. Same regex parsing pattern
2. Same offset range (-50 to +50°C)
3. Same websocket update structure
4. Same UI display (temprow template)
5. Same temperature graph integration

## Files Modified

### Backend
- `src/octoprint/util/comm.py` - Temperature parsing and storage
- `src/octoprint/printer/standard.py` - Temperature control and state
- `src/octoprint/printer/__init__.py` - Heater validation regex
- `src/octoprint/server/api/printer.py` - API endpoints

### Frontend  
- `src/octoprint/static/js/app/viewmodels/printerprofiles.js` - Profile UI
- `src/octoprint/static/js/app/client/printer.js` - JavaScript client
- `src/octoprint/static/js/app/viewmodels/temperature.js` - Temperature viewmodel
- `src/octoprint/templates/tabs/temperature.jinja2` - UI template

## Validation

All test cases pass for M105 parsing:
- ✓ Standard M105 with secondary heaters
- ✓ M105 with active heating
- ✓ M105 with all heater types (T, B, C, F, H)
- ✓ M105 with 4 secondary heaters
- ✓ M105 with no targets

The implementation correctly:
- Parses H0, H1, H2, etc. from M105 responses
- Only processes when `hasSecondaryHeaters` is enabled
- Matches heater count to extruder count
- Sends proper M104 H{n} S{temp} commands
- Provides complete API coverage
- Integrates with UI and websockets
