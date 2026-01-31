# v1.4.2 - Fix Entity Availability

## Issue Fixed
All entities remained UNAVAILABLE for 20 seconds after setup completion. Users saw broken/non-functional entities despite successful connection.

## Root Cause
The first device poll occurred only after the poll_interval elapsed (20 seconds). During this window, entities had no state data and remained UNAVAILABLE. Short debug logs (< 20s) showed "polling started" but no actual polls, leading to confusion.

## Solution
- Trigger immediate poll after connection establishment
- Entities become available instantly with populated state
- Subsequent polls continue every 20 seconds
- Improved error logging (DEBUG → ERROR level)
- Removed duplicate poll_interval property definition

## Who Should Upgrade
**ALL users running v1.3.8 through v1.4.1** experiencing UNAVAILABLE entities.

## Installation
Upload `uc-intg-eversolo-1.4.2-aarch64.tar.gz` to your Remote via Settings → Integrations → Add Integration → Upload driver.
