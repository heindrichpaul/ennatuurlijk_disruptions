# v2.0.0 Release Notes

## Major Refactor

- Centralized all data fetching and parsing logic in `fetch.py`.
- Added in-memory caching and background refresh for disruption data, using `MIN_TIME_BETWEEN_UPDATES` for refresh interval.
- All parsing and section logic is now modular and reusable.
- Sensor code is simplified and only handles Home Assistant entity logic.
- Logging is now fully centralized via `_LOGGER` from `const.py`.
- Translation and entity naming fully aligned with Home Assistant best practices.

## Breaking Changes

- Internal structure and code layout have changed significantly. No user-facing breaking changes expected, but custom automations/scripts relying on internal Python structure may need review.

## Performance and Maintenance Improvements

- Improved performance and reliability due to caching and background refresh.
- Easier maintenance and future feature development.

---

## v1.0.4 Release Notes

### Bugfixes

- Entity display names are now correctly translated in both English and Dutch, using Home Assistant's entity translation system.
- Updated sensor code to use `_attr_name` for proper translation key matching.
- Dutch translation file structure updated for consistency with English.

### Improvements

- Documentation and translation best practices clarified.
- No breaking changes; update is safe for all users.

---

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
