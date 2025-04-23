# Android Assessment Tool Backend

A FastAPI-based backend service for evaluating connected Android devices. This tool automatically detects device brand, runs fast and full scans via ADB, streams real-time status updates over WebSocket, and stores results in a SQLite database.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
  - [api/](#apifolder)
  - [service/](#servicefolder)
  - [repositories/](#repositoriesfolder)
  - [models/](#modelsfolder)
  - [database/](#databasefolder)
  - [static/](#staticfolder)
- [Key Components](#key-components)
- [Installation](#installation)
- [Usage](#usage)
  - [Running the Server](#running-the-server)
  - [API Docs](#api-docs)
  - [WebSocket Endpoint](#websocket-endpoint)
  - [Device Connection Endpoints](#device-connection-endpoints)
  - [Scanning Endpoints](#scanning-endpoints)
  - [Report Endpoints](#report-endpoints)
- [Database](#database)
- [Error Handling](#error-handling)
- [Extending the System](#extending-the-system)
- [License](#license)

## Overview
This backend powers an Android Assessment Tool that:

1. Detects when an Android device is connected via USB.
2. Identifies the device brand (e.g., Xiaomi, Infinix).  
3. Performs fast and full scans by issuing ADB commands (brand-specific patterns).  
4. Streams real-time status updates to the frontend over WebSocket.  
5. Persists scan results in SQLite for later retrieval and comparison.

## Architecture
```
Android-Assessment-Backend/
├── api/               # FastAPI routers for each feature
├── service/           # Business logic: device & scan services
├── repositories/      # Data access: ADB, database, brand implementations
│   └── brand/         # Brand-specific ADB command abstractions
├── models/            # Pydantic models for requests & responses
├── database/          # SQL schema & migrations
├── static/            # Static assets (e.g., report templates)
├── main.py            # App entrypoint, mounts routers & WebSocket
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

### Directory Details
- **api/**: Defines HTTP routes (device connection, fast/full scan, reports).
- **service/**: Implements `DeviceService` (polls and manages devices) and `ScanService` (orchestrates scans and persists results).
- **repositories/**: Contains
  - `ADBRepository`: Async wrapper around ADB CLI.
  - `DBRepository`: Async SQLite operations via aiosqlite.
  - **brand/**: `BaseBrand` abstract class and concrete classes (`XiaomiBrand`, `InfinixBrand`) plus `BrandFactory` to select implementation.
- **models/**: Pydantic schemas for type-safe API I/O.
- **database/**: `schema.sql` defines the `scans` table and indexes.
- **static/**: Holds unchanging resources; used for report templates if needed.

## Key Components
- **ADBRepository**: Runs shell commands on devices (`adb -s <id> shell ...`) asynchronously.
- **BaseBrand / BrandFactory**: Encapsulate brand-specific ADB command differences; auto-detects brand via `getprop`.
- **ScanService**: Orchestrates fast/full scans, sends WebSocket updates, saves results.
- **DeviceService**: Polls connected devices, handles authorization, broadcasts device connection events.
- **DBRepository**: Manages SQLite storage of scan results (CRUD).
- **WebSocket Manager**: Broadcasts JSON status messages to `/ws` clients in real time.

## Installation
```bash
git clone <repo-url>
cd Android-Assessment-Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
### Running the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Docs
Open Swagger UI at: `http://localhost:8000/docs`

### WebSocket Endpoint
- **URL**: `ws://localhost:8000/ws`  
Clients receive status updates:
```json
{ "type": "status_update", "message": "...", "timestamp": "..." }
```

### Device Connection Endpoints
- `POST /device/start-polling`: Begin polling for USB-connected devices.
- `POST /device/stop-polling`: Stop polling.
- `GET  /device/connected`: List currently connected devices.
- `GET  /device/{device_id}`: Get metadata for a device.
- `POST /device/wait?timeout=30`: Wait up to N seconds for a device.

### Scanning Endpoints
- `POST /scan/fast/{device_id}`: Trigger fast scan (basic info).
- `GET  /scan/fast/{device_id}/last`: Retrieve last fast scan.
- `POST /scan/full/{device_id}`: Trigger full scan (includes installed apps).
- `GET  /scan/full/{device_id}/last`: Retrieve last full scan.
- `GET  /scan/full/{device_id}/compare/{scan1}/{scan2}`: Compare two scans.

### Report Endpoints
- `GET    /reports/`: List recent scan reports.
- `GET    /reports/{scan_id}`: Get report by ID.
- `GET    /reports/device/{device_id}`: Reports for a device.
- `GET    /reports/{scan_id}/download?format=json`: Download JSON.
- `DELETE /reports/{scan_id}`: Delete a report.

## Database
Located at `database/scans.db` by default. Schema in `database/schema.sql`.

## Error Handling
- HTTP 4xx/5xx for invalid requests or scan/device errors.
- WebSocket provides real-time feedback for long-running scans.

## Extending the System
1. **Add Brand**: Implement `BaseBrand` methods in a new class under `repositories/brand/` and register it in `BrandFactory`.
2. **New Scan Feature**: Extend `ScanService` and add routes in `api/`.
3. **Custom Reports**: Add Jinja2 templates under `static/report_templates` and logic in `ReportService`.

## License
MIT License. See [LICENSE](LICENSE) for details.