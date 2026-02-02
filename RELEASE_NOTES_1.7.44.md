# OctoPrint 1.7.44 - Secondary Heaters Support

## 🎉 Major New Feature: Secondary Heaters

This release adds comprehensive support for **secondary heaters** (H0, H1, H2, etc.) for custom 3D printers. Secondary heaters are additional heating elements that can be controlled independently alongside your existing extruders, bed, chamber, and filament heaters.

### Key Features

✅ **Full M105 Integration** - Automatically parse H0, H1, H2, etc. from firmware temperature responses  
✅ **M104 Control Commands** - Send `M104 H0 S50` to set secondary heater temperatures  
✅ **REST API Endpoints** - Complete API for getting and setting secondary heater temperatures  
✅ **WebSocket Real-time Updates** - Live temperature monitoring via SockJS  
✅ **UI Integration** - Temperature controls, graphs, and offset adjustments in the web interface  
✅ **Temperature Offsets** - Support for -50°C to +50°C offsets  

---

## What's New

### 🔧 Configuration
- New printer profile setting: **"Has Secondary Heaters"** checkbox
- Secondary heater count automatically matches extruder count
- Enable in: Settings → Printer Profiles → Edit Profile

### 📊 Temperature Monitoring
When your firmware sends M105 responses like:
```
ok T0:200.0/200.0 T1:200.0/200.0 B:60.0/60.0 H0:75.0/80.0 H1:50.0/55.0
```

OctoPrint now:
- Parses H0, H1, H2, etc. parameters
- Displays them in the temperature tab
- Shows real-time graphs with auto-assigned colors
- Updates via WebSocket every 0.5 seconds

### 🎮 Temperature Control
- **UI Controls**: Set target temperatures and offsets from the temperature tab
- **API Endpoints**:
  - `GET /api/printer/heater/<num>` - Get heater state
  - `POST /api/printer/heater/<num>` - Set target or offset
- **G-code Commands**: `M104 H0 S75`, `M104 H1 S50`

### 🖥️ JavaScript Client
New methods available in `OctoPrint.printer`:
```javascript
OctoPrint.printer.setSecondaryHeaterTargetTemperature(0, 75);
OctoPrint.printer.setSecondaryHeaterTemperatureOffset(0, 5);
OctoPrint.printer.getSecondaryHeaterState(0);
```

---

## Technical Details

### Implementation Changes

#### Backend
- **comm.py**: Enhanced temperature regex to parse `H(?P<heaternum>\d*)` pattern
- **TemperatureRecord**: Added `_secondary_heaters` dict storage and accessors
- **standard.py**: 
  - New storage: `_secondaryHeatersTemp`, `_targetSecondaryHeatersTemp`
  - Updated `set_temperature()` to send M104 commands with H parameter
  - Extended `get_current_temperatures()` to include secondary heaters
  - Updated `_addTemperatureData()` for WebSocket integration
- **printer.py**: New API endpoints at `/api/printer/heater/<num>`

#### Frontend
- **printerprofiles.js**: Added `hasSecondaryHeaters` observable
- **client/printer.js**: New client methods for secondary heater control
- **temperature.js**: 
  - Observable array for secondary heaters
  - Auto-initialization based on extruder count
  - Graph integration with color assignment
  - Offset and target temperature handling
- **temperature.jinja2**: UI template rows for secondary heater display

### API Response Format

#### GET /api/printer
```json
{
  "temperature": {
    "tool0": {"actual": 200.0, "target": 200.0, "offset": 0},
    "bed": {"actual": 60.0, "target": 60.0, "offset": 0},
    "H0": {"actual": 75.2, "target": 75.0, "offset": 0},
    "H1": {"actual": 50.1, "target": 50.0, "offset": 0}
  }
}
```

#### WebSocket Message
```json
{
  "current": {
    "temps": [{
      "tool0": {"actual": 200.0, "target": 200.0},
      "bed": {"actual": 60.0, "target": 60.0},
      "H0": {"actual": 75.0, "target": 75.0},
      "H1": {"actual": 50.0, "target": 50.0},
      "time": 1769866024
    }]
  }
}
```

---

## Bug Fixes

- Fixed variable name collision in `_processTemperatures()` that could cause issues with secondary heater parsing
- Added safe default (`False`) for `hasSecondaryHeaters` printer profile setting

---

## Documentation

Complete documentation available in `SECONDARY_HEATERS_DOCUMENTATION.md` including:
- API endpoint reference with examples
- JavaScript client usage
- WebSocket message format
- M105 parsing details
- Comparison with other heater types
- Configuration instructions

---

## Upgrade Notes

### For Users
1. Update OctoPrint to version 1.7.44
2. Go to Settings → Printer Profiles
3. Edit your printer profile
4. Check "Has Secondary Heaters" if your firmware supports H parameters
5. Set your extruder count (secondary heaters will match)
6. Save and restart OctoPrint

### For Developers
- Secondary heaters use the H parameter in M104/M105 commands
- API endpoints follow the pattern `/api/printer/heater/<num>` (0-indexed)
- WebSocket updates automatically include H0, H1, etc. when configured
- Temperature data structure matches other heaters (actual, target, offset)

### Firmware Requirements
Your 3D printer firmware must:
- Return H parameters in M105 responses: `H0:25.0/0.0 H1:25.0/0.0`
- Accept M104 with H parameter: `M104 H0 S50`
- Number of H heaters should match extruder count

---

## Installation

### Via OctoPrint Plugin Manager
1. Settings → Software Update
2. Check for updates
3. Install version 1.7.44

### Manual Installation
```bash
pip install https://github.com/FracktalWorks/Fracktal_OctoPrint/archive/1.7.44.zip
```

---

## Testing

All integration tests pass:
- ✅ M105 parsing for H0-H9 parameters
- ✅ Temperature storage and retrieval
- ✅ API endpoint responses
- ✅ WebSocket message format
- ✅ UI display and controls

---

## Examples

### Set Secondary Heater via API
```bash
# Set H0 to 75°C
curl -X POST http://octopi.local/api/printer/heater/0 \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"target","target":75}'
```

### Set Secondary Heater via JavaScript
```javascript
OctoPrint.printer.setSecondaryHeaterTargetTemperature(0, 75)
  .done(function() {
    console.log("H0 set to 75°C");
  });
```

### Check Secondary Heater Temperature
```bash
# Get current state
curl -X GET http://octopi.local/api/printer/heater/0 \
  -H "X-Api-Key: YOUR_API_KEY"
```

---

## Credits

This feature was developed to support custom 3D printers with multiple heating zones, enabling precise temperature control for advanced printing applications.

## Support

For issues or questions:
- GitHub Issues: https://github.com/FracktalWorks/Fracktal_OctoPrint/issues
- Documentation: See `SECONDARY_HEATERS_DOCUMENTATION.md` in the repository

---

**Full Changelog**: https://github.com/FracktalWorks/Fracktal_OctoPrint/compare/1.7.43...1.7.44
