# v2.0.1 Release Notes

## Improvements & Fixes

- **Postal code matching**: Now matches disruptions for all common postal code formats: `1234`, `1234AB`, and `1234 AB` (space-separated), improving detection of disruptions regardless of how the code is entered on the Ennatuurlijk website.
- **Configurable update interval**: The update interval for fetching disruption data is now user-configurable via the integration options. Users can set the interval in minutes from the UI.
- **Disruption links in attributes**: If a disruption contains a link, it is now included in the `dates` and `disruptions` attributes for each sensor, allowing direct access to the disruption details from Home Assistant.
- **Translation updates**: English and Dutch translation files updated to include the new update interval option in all config and options forms.
- **Removed in-memory cache**: All local caching and background refresh logic has been removed. Data is now always fetched fresh at the configured interval, relying on Home Assistant's update coordinator.
- **Code cleanup**: Minor improvements to logging and error handling for maintainability.

---

# v2.0.0 Release Notes

## Major Refactor & Modernization

- **Complete modular restructure**: Centralized all data fetching and parsing logic in `fetch.py` with dedicated sensor files for better maintainability.
- **Enhanced performance**: Added in-memory caching and background refresh for disruption data with configurable refresh intervals.
- **Better sensor architecture**: Each sensor type (planned, current, solved) now has its own dedicated file with consistent state and attribute handling.
- **Alert sensors**: Boolean alert sensors are now fully backwards compatible with v1.x while providing improved functionality.
- **Translation fixes**: All config flow, options flow, and entity translations now work correctly in both English and Dutch.
- **User-configurable options**: Added options flow for configuring alert sensor creation and solved disruption retention days.
- **Robust error handling**: Improved error handling and edge case management throughout the integration.
- **Home Assistant best practices**: Full alignment with Home Assistant's translation system, entity naming, and integration patterns.

## New Features

- **Modular sensors**: Separate sensor files for planned, current, and solved disruptions with consistent attribute structure.
- **Options configuration**: Users can now configure integration options after setup via the UI.
- **Enhanced attributes**: All sensors now provide rich, consistent attributes including days until/since dates and boolean today indicators.
- **Last update tracking**: All sensors now display the exact date and time of last successful data fetch.
- **Configurable alert sensors**: Alert sensors can be enabled/disabled via options and provide backward compatibility.

## Compatibility & Migration

- **Backwards compatible**: Alert sensors maintain full compatibility with v1.x automations and scripts.
- **No breaking changes**: All existing entity IDs and sensor names remain unchanged.
- **Improved structure**: New sensors provide better structured data while maintaining compatibility.
- **Safe upgrade**: Update is completely safe for all existing users.

## Technical Improvements

- **Centralized logging**: All modules use consistent `_LOGGER` for debugging and troubleshooting.
- **Improved caching**: Smart in-memory caching with background refresh prevents API rate limiting.
- **Better date handling**: Enhanced date parsing and formatting with proper month name mapping.
- **Robust translation**: Complete translation support for all UI elements in English and Dutch.

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
