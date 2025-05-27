## v1.0.3 Release Notes

### Maintenance
- Translation files (en.json, nl.json) are now fully flat and validated for Home Assistant requirements.
- No functional changes, but improved compatibility and validation for HACS and Home Assistant.

---

## v1.0.2 Release Notes

### Features
- Sensor names are now translatable (Dutch and English supported).
- All disruption dates are now formatted as DD-MM-YYYY for language independence.
- Improved and anonymized documentation and example attributes in the README.

### Improvements
- HACS release zip now contains only the correct folder structure for easy installation.
- Manifest and configuration now fully comply with the latest HACS and Home Assistant requirements.
- README includes clear instructions for adding the integration as a custom repository in HACS.

### Bugfixes
- Fixed: Main sensor state is always 'on' or 'off' (never undefined).
- Fixed: Multiple disruptions per category are now correctly shown as a list of objects with description and date.
