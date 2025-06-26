# Ennatuurlijk Disruptions Integration
[![HACS Validation](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hacs.yaml/badge.svg)](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hacs.yaml)
[![Validate with hassfest](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hassfest.yaml)

A modern, fully translated Home Assistant integration to monitor Ennatuurlijk disruptions for a specified town or postal code. Features modular sensor architecture, configurable options, and comprehensive Dutch/English translation support.

## Installation
1. **HACS Installation**: Install via HACS by adding this repository as a custom repository: `https://github.com/heindrichpaul/ennatuurlijk_disruptions`.
2. **Configuration**: Go to Settings > Devices & Services > Add Integration, select "Ennatuurlijk Disruptions", and enter your town and postal code.
3. **Options**: After setup, click "Configure" to access additional options like alert sensor creation, solved disruption retention, and update interval settings.

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
- **Configurable Update Interval**: Set how often data is refreshed (in minutes) via the integration options
- **No Local Caching**: Always fetches fresh data at the configured interval (no in-memory cache)
- **Disruption Links**: If a disruption contains a link, it is included in the `dates` and `disruptions` attributes for direct access
- **Flexible Postal Code Matching**: Matches disruptions for all common postal code formats: `1234`, `1234AB`, and `1234 AB`
- **Rich Attributes**: Each sensor provides comprehensive attributes including days until/since dates
- **Configurable Options**: Customize alert sensor creation, solved disruption retention, and update interval via UI
- **Full Translation Support**: Complete Dutch and English translations for all UI elements
- **Backwards Compatibility**: v1.x alert sensors remain fully functional
- **Multiple Disruption Support**: Handle multiple disruptions per category with detailed information
- **Date Intelligence**: Smart date parsing and closest date calculation for sensor states
- **Real-time Updates**: Manual update capability via Home Assistant UI
- **Location Matching**: Flexible matching by town name or postal code (full, partial, or spaced)

## Requirements

- Home Assistant 2023.3.0 or later
- Python libraries: `requests`, `beautifulsoup4` (automatically installed)

## Configuration Options

After initial setup, click "Configure" on the integration to access:

- **Enable Alert Sensors**: Create boolean sensors for automation compatibility
- **Solved Disruption Retention**: Number of days to keep solved disruptions (default: 7)
- **Update Interval**: How often to fetch new data (in minutes, default: 120)

## Sensor Attributes

Each sensor provides rich attributes for automation and display purposes:

### Main Sensors
- `state`: Closest relevant date (YYYY-MM-DD format) or None
- `dates`: List of all disruptions with description, date, and (if available) a `link` to the disruption
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
        link: "https://ennatuurlijk.nl/storingen/1234"
      - description: "Example planned disruption 2"  
        date: "25-06-2025"
        link: null
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
- **Disruption Links**: Use the `link` field in the `dates` attribute to access disruption details directly
- **Flexible Matching**: Disruptions are matched by town, full postal code, partial, or spaced format

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

**Current Version**: 2.0.3

**Changelog**: See [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed release information

## Calendar Integration

- **Single calendar entity**: All planned, current, and solved disruptions are shown in a single calendar entity.
- **One event per disruption**: Each disruption is represented by a single event, updated in place as its status changes (planned → current → solved).
- **Solved-only events**: If a disruption is only present as solved (e.g., integration installed after the event), it is shown as a single all-day event with status `solved`.
- **Clean event descriptions**: Event descriptions only include the status (as a hashtag, e.g. `#planned`, `#current`, `#solved`) and the disruption link, making them easy to use in automations and readable in the UI.
- **Status hashtag for automations**: The status in the description is always one of `#planned`, `#current`, or `#solved`. You can use this in automations to trigger actions based on disruption status.

### Example: Automation using calendar event status hashtag

```yaml
automation:
  - alias: "Notify on Current Disruption Event"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.ennatuurlijk_disruptions_calendar
    condition:
      - condition: template
        value_template: >
          {{ '#current' in trigger.calendar_event.description }}
    action:
      - service: notify.mobile_app
        data:
          message: "A current disruption has started: {{ trigger.calendar_event.summary }}"
```
