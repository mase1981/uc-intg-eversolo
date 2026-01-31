# v1.4.3 - Fix Entity Update Event Error

## Issue Fixed
v1.4.2 was completely broken - polling occurred but all entities remained UNAVAILABLE or showed UNKNOWN states. Logs showed recurring error: `BaseIntegrationDriver.on_device_update() missing 1 required positional argument: 'entity_id'`.

## Root Cause
The UPDATE event was emitted with a keyword argument:
```python
self.events.emit(DeviceEvents.UPDATE, update={})
```

The framework's `BaseIntegrationDriver` is also subscribed to device UPDATE events and expects `entity_id` as the first positional argument. The keyword argument caused a signature mismatch, throwing TypeError on every poll attempt.

## Solution
Emit UPDATE event without arguments:
```python
self.events.emit(DeviceEvents.UPDATE)
```

Entity handlers accept `**kwargs`, so they work correctly. The driver handler no longer receives mismatched parameters.

## Who Should Upgrade
**CRITICAL for ALL v1.4.2 users** - v1.4.2 is completely broken and should not be used.

## Installation
Upload `uc-intg-eversolo-1.4.3-aarch64.tar.gz` to your Remote via Settings → Integrations → Add Integration → Upload driver.
