# RDP2TCP Enhanced Features

This document describes the new enhanced features added to RDP2TCP.

## 1. Enhanced CLI Tools

The new `rdp2tcp-cli.py` provides a modern command-line interface with improved usability and configuration management.

### Features

- **Configuration Management**: Support for YAML and JSON configuration files
- **Structured Commands**: Organized subcommands for better usability
- **Multiple Output Formats**: Table, JSON, and YAML output formats
- **Real-time Monitoring**: Live tunnel status monitoring
- **Logging Integration**: Built-in logging with configurable levels

### Usage Examples

```bash
# Create a tunnel with compression
rdp2tcp-cli --config config.yaml tunnel create \
  --name web-server \
  --type tcp \
  --local 8080 \
  --remote 80 \
  --compression gzip

# List tunnels in JSON format
rdp2tcp-cli tunnel list --format json

# Monitor tunnels for 5 minutes
rdp2tcp-cli monitor --duration 300

# Save current configuration
rdp2tcp-cli config save --output my-config.yaml
```

### Configuration File Example

```yaml
# config.yaml
controller_host: "127.0.0.1"
controller_port: 8477
log_level: "INFO"
log_file: "rdp2tcp-cli.log"

tunnels:
  - name: "web-server"
    type: "tcp"
    local_host: "127.0.0.1"
    local_port: 8080
    remote_host: "192.168.1.100"
    remote_port: 80
    enabled: true
    compression: "gzip"
    bandwidth_limit: 1048576  # 1MB/s

  - name: "ssh-access"
    type: "reverse"
    local_host: "127.0.0.1"
    local_port: 2222
    remote_host: "192.168.1.100"
    remote_port: 22
    enabled: true
    compression: "lz4"
```

## 2. Compression Support

RDP2TCP now supports data compression to reduce bandwidth usage and improve performance.

### Supported Algorithms

- **GZIP**: High compression ratio, slower compression
- **LZ4**: Fast compression/decompression, lower compression ratio
- **None**: No compression (default)

### Protocol Changes

New compression command added to the protocol:

```c
#define R2TCMD_COMPRESS 0x06

typedef struct _r2tmsg_compress {
    unsigned char cmd;      // R2TCMD_COMPRESS
    unsigned char id;       // tunnel identifier
    unsigned char algorithm; // compression algorithm
    unsigned char level;    // compression level
    unsigned int original_size; // original data size
    char data[0];          // compressed data
} r2tmsg_compress_t;
```

### Compression Levels

- **GZIP**: 1-9 (1=fast, 9=best compression)
- **LZ4**: 1-16 (1=fast, 16=best compression)

### Usage

Compression can be enabled per tunnel:

```bash
# Create tunnel with gzip compression
rdp2tcp-cli tunnel create --name compressed-tunnel \
  --type tcp --local 8080 --remote 80 \
  --compression gzip

# Create tunnel with LZ4 compression
rdp2tcp-cli tunnel create --name fast-tunnel \
  --type tcp --local 8081 --remote 80 \
  --compression lz4
```

### Automatic Compression

The system automatically determines if compression would be beneficial:

- Skips compression for small data (< 64 bytes)
- Analyzes data patterns to avoid compressing already compressed data
- Provides compression statistics in logs

## 3. Advanced Logging System

A comprehensive logging system with structured logging, multiple output formats, and log rotation.

### Features

- **Multiple Log Levels**: DEBUG, INFO, WARN, ERROR, AUDIT
- **Log Categories**: GENERAL, NETWORK, TUNNEL, CHANNEL, SECURITY, PERFORMANCE
- **Output Formats**: Text, JSON, Syslog
- **Destinations**: Stdout, Stderr, File, Syslog
- **Log Rotation**: Automatic file rotation with size limits
- **Thread Safety**: Thread-safe logging with mutex protection
- **Color Output**: Colored output for terminal display

### Log Levels

```c
typedef enum {
    LOG_LEVEL_DEBUG = 0,   // Detailed debugging information
    LOG_LEVEL_INFO,        // General information
    LOG_LEVEL_WARN,        // Warning messages
    LOG_LEVEL_ERROR,       // Error messages
    LOG_LEVEL_AUDIT,       // Security audit events
    LOG_LEVEL_MAX
} log_level_t;
```

### Log Categories

```c
typedef enum {
    LOG_CAT_GENERAL = 0,   // General application events
    LOG_CAT_NETWORK,       // Network-related events
    LOG_CAT_TUNNEL,        // Tunnel-specific events
    LOG_CAT_CHANNEL,       // RDP channel events
    LOG_CAT_SECURITY,      // Security-related events
    LOG_CAT_PERFORMANCE,   // Performance metrics
    LOG_CAT_MAX
} log_category_t;
```

### Usage Examples

#### Basic Logging

```c
#include "logger.h"

// Initialize logger
logger_config_t config = {
    .level = LOG_LEVEL_INFO,
    .format = LOG_FORMAT_TEXT,
    .destination = LOG_DEST_STDOUT,
    .enable_timestamp = 1,
    .enable_color = 1
};
logger_init(&config);

// Log messages
LOG_INFO(LOG_CAT_GENERAL, "Application started");
LOG_WARN(LOG_CAT_NETWORK, "Connection timeout");
LOG_ERROR(LOG_CAT_TUNNEL, "Tunnel creation failed");
```

#### Structured Logging

```c
// Log with structured data
log_structured(LOG_LEVEL_INFO, LOG_CAT_TUNNEL, 
               "tunnel.c", "tunnel_create", 123,
               "tunnel-01", "compression=gzip",
               "Tunnel created successfully");

// Log tunnel-specific events
log_tunnel(LOG_LEVEL_INFO, "tunnel-01", "Data transfer started");

// Log security events
log_security(LOG_LEVEL_WARN, "auth_failure", "192.168.1.100",
             "invalid_credentials", "Authentication failed");
```

#### Performance Logging

```c
// Log performance metrics
log_performance("bandwidth", 1024.5, "KB/s", "tunnel-01");
log_performance("latency", 45.2, "ms", "tunnel-01");
```

#### Audit Logging

```c
// Log audit events
log_audit("admin", "tunnel_create", "tunnel-01", "success", 
          "Tunnel created via CLI");
log_audit("user1", "tunnel_delete", "tunnel-02", "failure", 
          "Permission denied");
```

### Configuration

```c
logger_config_t config = {
    .level = LOG_LEVEL_INFO,
    .format = LOG_FORMAT_JSON,
    .destination = LOG_DEST_FILE,
    .filename = "rdp2tcp.log",
    .max_file_size = 10 * 1024 * 1024,  // 10MB
    .max_files = 5,                      // Keep 5 backup files
    .enable_timestamp = 1,
    .enable_thread_id = 1,
    .enable_color = 0                    // Disable for file output
};
```

### Output Formats

#### Text Format
```
2024-01-15 14:30:25 [12345] [INFO] [TUNNEL] Tunnel created successfully
2024-01-15 14:30:26 [12345] [WARN] [NETWORK] Connection timeout
```

#### JSON Format
```json
{
  "timestamp": "2024-01-15 14:30:25",
  "level": "INFO",
  "category": "TUNNEL",
  "module": "tunnel.c",
  "function": "tunnel_create",
  "line": 123,
  "message": "Tunnel created successfully",
  "tunnel_id": "tunnel-01",
  "details": "compression=gzip",
  "thread_id": "12345"
}
```

### Log Rotation

The logging system automatically rotates log files when they reach the configured size limit:

- Current log file: `rdp2tcp.log`
- Backup files: `rdp2tcp.log.1`, `rdp2tcp.log.2`, etc.
- Oldest backup file is deleted when max_files is reached

## Building with New Features

### Dependencies

```bash
# Install required packages
sudo apt-get install libz-dev liblz4-dev python3-yaml

# For development
sudo apt-get install python3-dev
```

### Compilation

```bash
# Build with compression support
make CFLAGS="-DHAVE_LZ4" LDFLAGS="-lz -llz4"

# Build without LZ4 (gzip only)
make CFLAGS="" LDFLAGS="-lz"
```

### Python Dependencies

```bash
# Install Python dependencies for enhanced CLI
pip3 install pyyaml
```

## Integration

These features integrate seamlessly with the existing RDP2TCP codebase:

1. **Backward Compatibility**: All new features are optional and don't break existing functionality
2. **Gradual Migration**: Can be enabled per tunnel or globally
3. **Performance Monitoring**: Built-in metrics for compression effectiveness
4. **Security**: Audit logging for compliance requirements

## Future Enhancements

Planned improvements for these features:

1. **Compression**: Add more algorithms (Zstandard, Brotli)
2. **Logging**: Add log aggregation and analysis tools
3. **CLI**: Add interactive mode and web-based management interface
4. **Performance**: Add bandwidth throttling and QoS features
