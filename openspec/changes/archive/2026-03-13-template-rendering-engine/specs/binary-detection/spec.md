## ADDED Requirements

### Requirement: Binary file detection
The system SHALL detect binary files and skip Jinja2 rendering for them, copying them raw instead.

#### Scenario: Detect PNG as binary
- **WHEN** a file named `logo.png` is encountered
- **THEN** it is detected as binary via extension blocklist and copied raw

#### Scenario: Detect binary by content
- **WHEN** a file with unknown extension contains null bytes in the first 8192 bytes
- **THEN** it is detected as binary and copied raw

#### Scenario: Text file not falsely detected
- **WHEN** a `.py` file contains only valid UTF-8 text
- **THEN** it is detected as text and eligible for rendering

### Requirement: Extension blocklist
The system SHALL maintain a blocklist of known binary file extensions that are detected without reading file content.

#### Scenario: Known binary extensions
- **WHEN** a file has extension `.png`, `.jpg`, `.gif`, `.zip`, `.exe`, `.woff2`, `.ttf`, `.so`, or `.dylib`
- **THEN** it is classified as binary without reading the file
