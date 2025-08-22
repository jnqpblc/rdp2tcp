/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
#ifndef __RDP2TCP_LOGGER_H__
#define __RDP2TCP_LOGGER_H__

#include <time.h>
#include <stdarg.h>

// Log levels
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARN,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_AUDIT,
    LOG_LEVEL_MAX
} log_level_t;

// Log categories
typedef enum {
    LOG_CAT_GENERAL = 0,
    LOG_CAT_NETWORK,
    LOG_CAT_TUNNEL,
    LOG_CAT_CHANNEL,
    LOG_CAT_SECURITY,
    LOG_CAT_PERFORMANCE,
    LOG_CAT_MAX
} log_category_t;

// Log output formats
typedef enum {
    LOG_FORMAT_TEXT = 0,
    LOG_FORMAT_JSON,
    LOG_FORMAT_SYSLOG,
    LOG_FORMAT_MAX
} log_format_t;

// Log destination types
typedef enum {
    LOG_DEST_STDOUT = 0,
    LOG_DEST_STDERR,
    LOG_DEST_FILE,
    LOG_DEST_SYSLOG,
    LOG_DEST_MAX
} log_dest_t;

// Structured log entry
typedef struct {
    time_t timestamp;
    log_level_t level;
    log_category_t category;
    const char *module;
    const char *function;
    int line;
    const char *message;
    const char *tunnel_id;
    const char *details;
} log_entry_t;

// Logger configuration
typedef struct {
    log_level_t level;
    log_format_t format;
    log_dest_t destination;
    char *filename;
    int max_file_size;  // in bytes, 0 for unlimited
    int max_files;      // number of backup files, 0 for unlimited
    int enable_timestamp;
    int enable_thread_id;
    int enable_color;
} logger_config_t;

/**
 * Initialize the logging system
 * @param[in] config Logger configuration
 * @return 0 on success, negative value on error
 */
int logger_init(const logger_config_t *config);

/**
 * Cleanup the logging system
 */
void logger_cleanup(void);

/**
 * Set log level
 * @param[in] level New log level
 */
void logger_set_level(log_level_t level);

/**
 * Set log format
 * @param[in] format New log format
 */
void logger_set_format(log_format_t format);

/**
 * Log a message with structured data
 * @param[in] level Log level
 * @param[in] category Log category
 * @param[in] module Module name
 * @param[in] function Function name
 * @param[in] line Line number
 * @param[in] tunnel_id Tunnel ID (optional)
 * @param[in] details Additional details (optional)
 * @param[in] fmt Format string
 * @param[in] ... Variable arguments
 */
void log_structured(log_level_t level, log_category_t category,
                   const char *module, const char *function, int line,
                   const char *tunnel_id, const char *details,
                   const char *fmt, ...);

/**
 * Log a message with tunnel context
 * @param[in] level Log level
 * @param[in] tunnel_id Tunnel ID
 * @param[in] fmt Format string
 * @param[in] ... Variable arguments
 */
void log_tunnel(log_level_t level, const char *tunnel_id, const char *fmt, ...);

/**
 * Log a security event
 * @param[in] level Log level
 * @param[in] event Security event type
 * @param[in] source Source IP/host
 * @param[in] details Event details
 * @param[in] fmt Format string
 * @param[in] ... Variable arguments
 */
void log_security(log_level_t level, const char *event, const char *source,
                 const char *details, const char *fmt, ...);

/**
 * Log performance metrics
 * @param[in] metric Metric name
 * @param[in] value Metric value
 * @param[in] unit Unit of measurement
 * @param[in] tunnel_id Tunnel ID (optional)
 */
void log_performance(const char *metric, double value, const char *unit,
                    const char *tunnel_id);

/**
 * Log audit event
 * @param[in] user User performing action
 * @param[in] action Action performed
 * @param[in] resource Resource affected
 * @param[in] result Success/failure
 * @param[in] details Additional details
 */
void log_audit(const char *user, const char *action, const char *resource,
               const char *result, const char *details);

/**
 * Get log level name
 * @param[in] level Log level
 * @return Level name string
 */
const char *get_log_level_name(log_level_t level);

/**
 * Get log category name
 * @param[in] category Log category
 * @return Category name string
 */
const char *get_log_category_name(log_category_t category);

// Convenience macros for logging
#define LOG_DEBUG(cat, fmt, ...) \
    log_structured(LOG_LEVEL_DEBUG, cat, __FILE__, __func__, __LINE__, \
                   NULL, NULL, fmt, ##__VA_ARGS__)

#define LOG_INFO(cat, fmt, ...) \
    log_structured(LOG_LEVEL_INFO, cat, __FILE__, __func__, __LINE__, \
                   NULL, NULL, fmt, ##__VA_ARGS__)

#define LOG_WARN(cat, fmt, ...) \
    log_structured(LOG_LEVEL_WARN, cat, __FILE__, __func__, __LINE__, \
                   NULL, NULL, fmt, ##__VA_ARGS__)

#define LOG_ERROR(cat, fmt, ...) \
    log_structured(LOG_LEVEL_ERROR, cat, __FILE__, __func__, __LINE__, \
                   NULL, NULL, fmt, ##__VA_ARGS__)

#define LOG_TUNNEL_DEBUG(tid, fmt, ...) \
    log_tunnel(LOG_LEVEL_DEBUG, tid, fmt, ##__VA_ARGS__)

#define LOG_TUNNEL_INFO(tid, fmt, ...) \
    log_tunnel(LOG_LEVEL_INFO, tid, fmt, ##__VA_ARGS__)

#define LOG_TUNNEL_WARN(tid, fmt, ...) \
    log_tunnel(LOG_LEVEL_WARN, tid, fmt, ##__VA_ARGS__)

#define LOG_TUNNEL_ERROR(tid, fmt, ...) \
    log_tunnel(LOG_LEVEL_ERROR, tid, fmt, ##__VA_ARGS__)

#endif // __RDP2TCP_LOGGER_H__
