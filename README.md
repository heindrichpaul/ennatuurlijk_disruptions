# Ennatuurlijk Disruptions Integration
[![HACS Validation](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hacs.yaml/badge.svg)](https://github.com/heindrichpaul/ennatuurlijk_disruptions/actions/workflows/hacs.yaml)

A Home Assistant integration to monitor Ennatuurlijk disruptions for a specified town or postal code.

## Installation
1. Install via HACS by adding this repository as a custom repository: `https://github.com/heindrichpaul/ennatuurlijk_disruptions`.
2. Go to Settings > Devices & Services > Add Integration, select "Ennatuurlijk Disruptions", and enter your town and postal code (both required).
3. The integration will create the following sensors:
   - `sensor.ennatuurlijk_disruptions`: Main status sensor ("on" if planned or current disruptions, "off" otherwise)
   - `sensor.ennatuurlijk_planned_disruption`: Shows if there are planned disruptions (state: true/false, attribute: list of disruptions with description and date)
   - `sensor.ennatuurlijk_current_disruption`: Shows if there are current disruptions (state: true/false, attribute: list of disruptions with description and date)
   - `sensor.ennatuurlijk_solved_disruption`: Shows if there are solved disruptions (state: true/false, attribute: list of disruptions with description and date)
   - `sensor.ennatuurlijk_disruption_details`: Shows a summary of all disruptions

## Features
- Monitors current, planned, and solved disruptions from https://ennatuurlijk.nl/storingen.
- Matches disruptions by town or postal code (full or partial, e.g., 4105 for 4105TK).
- Updates every hour.
- Supports multiple disruptions per category, with each disruption's description and date available as attributes.

## Requirements
- Home Assistant 2023.3.0 or later.
- Python libraries: `requests`, `beautifulsoup4`.

## Configuration
- **Name**: A name for the integration (default: "Ennatuurlijk Disruptions").
- **Town**: Your town (required, no default).
- **Postal Code**: Your postal code (required, no default).

## Example Sensor Attributes
```
planned:
  state: true
  dates:
    - description: "Example planned disruption 1"
      date: "23 mei 2025"
    - description: "Example planned disruption 2"
      date: "23 mei 2025"
current:
  state: false
  dates: []
solved:
  state: true
  dates:
    - description: "Example solved disruption"
      date: "22 mei 2025"
details: |
  Planned disruption: Example planned disruption 1 (23 mei 2025)
  Planned disruption: Example planned disruption 2 (23 mei 2025)
  Solved disruption: Example solved disruption (22 mei 2025)
disruptions:
  - title: "Example planned disruption 1"
    date: "23 mei 2025"
    status: planned
  - title: "Example planned disruption 2"
    date: "23 mei 2025"
    status: planned
  - title: "Example solved disruption"
    date: "22 mei 2025"
    status: solved
town: "<your town>"
postal_code: "<your postal code>"
```

## Displaying Multiple Disruptions
- Each category sensor (`planned`, `current`, `solved`) exposes a `dates` attribute, which is a list of objects with `description` and `date`.
- Use a Lovelace Entities or Markdown card to display all disruptions for a category.

## Troubleshooting
- If you see "off" for the main sensor but have disruptions, check the attributes for details.
- For multiple disruptions, all are listed in the `dates` attribute for each category sensor.

## Version
- Integration version: 0.9.0