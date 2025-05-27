# Ennatuurlijk Disruptions Integration

A Home Assistant integration to monitor Ennatuurlijk disruptions for a specified town or postal code.

## Installation
1. Install via HACS by adding this repository as a custom repository: `https://github.com/heindrichpaul/ennatuurlijk_disruptions`.
2. Go to Settings > Devices & Services > Add Integration, select "Ennatuurlijk Disruptions", and enter your town and postal code (both required).
3. The sensor (`sensor.ennatuurlijk_disruptions`) will show disruptions with attributes: `planned`, `current`, `solved`, `details`, `dates`, `town`, and `postal_code`.

## Features
- Monitors current, planned, and solved disruptions from https://ennatuurlijk.nl/storingen.
- Matches disruptions by town or postal code (full or partial, e.g., 4105 for 4105TK).
- Updates every hour.

## Requirements
- Home Assistant 2023.3.0 or later.
- Python libraries: `requests`, `beautifulsoup4`.

## Configuration
- **Name**: A name for the integration (default: "Ennatuurlijk Disruptions").
- **Town**: Your town (required, no default).
- **Postal Code**: Your postal code (required, no default).

## Example Attributes
```json
{
  "planned": false,
  "current": false,
  "solved": true,
  "details": "Solved disruption: <town> <postal_code> (23 mei 2025)\n",
  "dates": ["Solved: <town> <postal_code> - 23 mei 2025"],
  "town": "<town>",
  "postal_code": "<postal_code>"
}
```