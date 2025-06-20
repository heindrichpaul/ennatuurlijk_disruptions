# Ennatuurlijk Disruptions Integration
[![HACS Validation](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hacs.yaml/badge.svg)](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hacs.yaml)
[![Validate with hassfest](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hassfest.yaml)

A modern, fully translated Home Assistant integration to monitor Ennatuurlijk disruptions for a specified town or postal code. Features modular sensor architecture, configurable options, and comprehensive Dutch/English translation support.

## Installation
1. **HACS Installation**: Install via HACS by adding this repository as a custom repository: `https://github.com/heindrichpaul/ennatuurlijk_disruptions`.
2. **Configuration**: Go to Settings > Devices & Services > Add Integration, select "Ennatuurlijk Disruptions", and enter your town and postal code.
3. **Options**: After setup, click "Configure" to access additional options like alert sensor creation and solved disruption retention settings.

## Sensors Created
The integration creates the following sensors with rich attributes and translations:

### Main Sensors
- **`sensor.ennatuurlijk_disruptions_planned`**: Planned disruptions (state: closest future date or None)
- **`sensor.ennatuurlijk_disruptions_current`**: Current disruptions (state: closest date or None)  
- **`sensor.ennatuurlijk_disruptions_solved`**: Solved disruptions (state: closest date or None)

### Alert Sensors (Optional)
- **`sensor.ennatuurlijk_disruptions_planned_alert`**: Boolean sensor for planned disruptions (on/off)
- **`sensor.ennatuurlijk_disruptions_current_alert`**: Boolean sensor for current disruptions (on/off)
- **`sensor.ennatuurlijk_disruptions_solved_alert`**: Boolean sensor for solved disruptions (on/off)

*Note: Alert sensors are backwards compatible with v1.x and can be enabled/disabled via integration options.*

## Features

- **Modern Architecture**: Modular sensor design with dedicated files for each disruption type
- **Smart Caching**: In-memory caching with background refresh prevents API rate limiting
- **Rich Attributes**: Each sensor provides comprehensive attributes including days until/since dates
- **Configurable Options**: Customize alert sensor creation and solved disruption retention via UI
- **Full Translation Support**: Complete Dutch and English translations for all UI elements
- **Backwards Compatibility**: v1.x alert sensors remain fully functional
- **Multiple Disruption Support**: Handle multiple disruptions per category with detailed information
- **Date Intelligence**: Smart date parsing and closest date calculation for sensor states
- **Real-time Updates**: Configurable refresh intervals with manual update capability
- **Location Matching**: Flexible matching by town name or postal code (full or partial)

## Requirements

- Home Assistant 2023.3.0 or later
- Python libraries: `requests`, `beautifulsoup4` (automatically installed)

## Configuration Options

After initial setup, click "Configure" on the integration to access:

- **Enable Alert Sensors**: Create boolean sensors for automation compatibility
- **Solved Disruption Retention**: Number of days to keep solved disruptions (default: 7)

## Sensor Attributes

Each sensor provides rich attributes for automation and display purposes:

### Main Sensors
- `state`: Closest relevant date (YYYY-MM-DD format) or None
- `dates`: List of all disruptions with description and date
- `last_update`: Timestamp of last successful data fetch
- `days_until_planned_date` / `days_since_*_date`: Calculated day differences
- `is_*_date_today`: Boolean indicating if disruption date is today

## Example Sensor Data

```yaml
# Planned Disruption Sensor
sensor.ennatuurlijk_disruptions_planned:
  state: "2025-06-23"  # Closest future date
  attributes:
    dates:
      - description: "Example planned disruption 1"
        date: "23-06-2025"
      - description: "Example planned disruption 2"  
        date: "25-06-2025"
    last_update: "2025-06-16 14:30"
    days_until_planned_date: 7
    is_planned_date_today: false

# Alert Sensor (if enabled)
sensor.ennatuurlijk_disruptions_planned_alert:
  state: "on"  # on if disruptions exist, off otherwise
```

## Automation Examples

### Get Notified of New Planned Disruptions

```yaml
automation:
  - alias: "Notify on Planned Disruptions"
    trigger:
      - platform: state
        entity_id: sensor.ennatuurlijk_disruptions_planned_alert
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "New planned disruption: {{ state_attr('sensor.ennatuurlijk_disruptions_planned', 'dates')[0].description }}"
```

## Usage Tips

- **Multiple Disruptions**: All disruptions are listed in the `dates` attribute for each sensor
- **Date Format**: Sensor states use YYYY-MM-DD format for consistency with Home Assistant
- **Alert Sensors**: Use alert sensors (on/off) for simple automation triggers
- **Rich Data**: Main sensors provide detailed date calculations and metadata

## Troubleshooting

- **No Data**: Verify your town and postal code match exactly with Ennatuurlijk's database
- **Missing Translations**: Clear browser cache (Cmd+Shift+R) and restart Home Assistant
- **Alert Sensors Missing**: Enable them via integration options after setup
- **Old Sensor Names**: v2.0 uses new naming - old sensors remain for compatibility

## Migration from v1.x

- **Automatic**: All existing automations continue to work unchanged
- **New Features**: Access new sensors and options via the integration configuration
- **No Breaking Changes**: Update safely without modifying automations

## Version

**Current Version**: 2.0.0

**Changelog**: See [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed release information
