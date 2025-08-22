/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
#include "logger.h"
#include "debug.h"
#include "print.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <unistd.h>
#include <pthread.h>

#ifdef HAVE_SYSLOG
#include <syslog.h>
#endif

// Global logger state
static struct {
    logger_config_t config;
    FILE *log_file;
    pthread_mutex_t mutex;
    int initialized;
} logger_state = {0};

// Color codes for terminal output
static const char *color_codes[] = {
    "\033[36m",  // DEBUG - cyan
    "\033[32m",  // INFO - green
    "\033[33m",  // WARN - yellow
    "\033[31m",  // ERROR - red
    "\033[35m"   // AUDIT - magenta
};

static const char *color_reset = "\033[0m";

// Log level names
static const char *level_names[] = {
    "DEBUG",
    "INFO",
    "WARN",
    "ERROR",
    "AUDIT"
};

// Log category names
static const char *category_names[] = {
    "GENERAL",
    "NETWORK",
    "TUNNEL",
    "CHANNEL",
    "SECURITY",
    "PERFORMANCE"
};

/**
 * Get current timestamp string
 */
static void get_timestamp(char *buffer, size_t size)
{
    time_t now;
    struct tm *tm_info;
    
    time(&now);
    tm_info = localtime(&now);
    
    strftime(buffer, size, "%Y-%m-%d %H:%M:%S", tm_info);
}

/**
 * Get thread ID string
 */
static void get_thread_id(char *buffer, size_t size)
{
#ifdef _WIN32
    snprintf(buffer, size, "%lu", GetCurrentThreadId());
#else
    snprintf(buffer, size, "%lu", (unsigned long)pthread_self());
#endif
}

/**
 * Rotate log file if needed
 */
static void rotate_log_file(void)
{
    if (!logger_state.config.filename || 
        logger_state.config.max_file_size <= 0) {
        return;
    }
    
    struct stat st;
    if (stat(logger_state.config.filename, &st) == 0) {
        if (st.st_size >= logger_state.config.max_file_size) {
            // Close current file
            if (logger_state.log_file) {
                fclose(logger_state.log_file);
                logger_state.log_file = NULL;
            }
            
            // Rotate existing backup files
            if (logger_state.config.max_files > 0) {
                char old_name[256], new_name[256];
                int i;
                
                for (i = logger_state.config.max_files - 1; i > 0; i--) {
                    snprintf(old_name, sizeof(old_name), "%s.%d", 
                             logger_state.config.filename, i);
                    snprintf(new_name, sizeof(new_name), "%s.%d", 
                             logger_state.config.filename, i + 1);
                    
                    if (access(old_name, F_OK) == 0) {
                        rename(old_name, new_name);
                    }
                }
                
                // Move current file to .1
                snprintf(new_name, sizeof(new_name), "%s.1", 
                         logger_state.config.filename);
                rename(logger_state.config.filename, new_name);
            }
            
            // Reopen log file
            logger_state.log_file = fopen(logger_state.config.filename, "a");
        }
    }
}

/**
 * Format log message as text
 */
static void format_text(const log_entry_t *entry, char *buffer, size_t size)
{
    char timestamp[64] = "";
    char thread_id[32] = "";
    const char *color_start = "";
    const char *color_end = "";
    
    if (logger_state.config.enable_timestamp) {
        get_timestamp(timestamp, sizeof(timestamp));
    }
    
    if (logger_state.config.enable_thread_id) {
        get_thread_id(thread_id, sizeof(thread_id));
    }
    
    if (logger_state.config.enable_color && 
        logger_state.config.destination == LOG_DEST_STDOUT) {
        color_start = color_codes[entry->level];
        color_end = color_reset;
    }
    
    snprintf(buffer, size,
             "%s%s%s [%s] [%s] %s%s%s",
             timestamp,
             timestamp[0] ? " " : "",
             thread_id,
             level_names[entry->level],
             category_names[entry->category],
             color_start,
             entry->message,
             color_end);
}

/**
 * Format log message as JSON
 */
static void format_json(const log_entry_t *entry, char *buffer, size_t size)
{
    char timestamp[64] = "";
    char thread_id[32] = "";
    
    if (logger_state.config.enable_timestamp) {
        get_timestamp(timestamp, sizeof(timestamp));
    }
    
    if (logger_state.config.enable_thread_id) {
        get_thread_id(thread_id, sizeof(thread_id));
    }
    
    snprintf(buffer, size,
             "{"
             "\"timestamp\":\"%s\","
             "\"level\":\"%s\","
             "\"category\":\"%s\","
             "\"module\":\"%s\","
             "\"function\":\"%s\","
             "\"line\":%d,"
             "\"message\":\"%s\","
             "\"tunnel_id\":\"%s\","
             "\"details\":\"%s\","
             "\"thread_id\":\"%s\""
             "}",
             timestamp,
             level_names[entry->level],
             category_names[entry->category],
             entry->module ? entry->module : "",
             entry->function ? entry->function : "",
             entry->line,
             entry->message,
             entry->tunnel_id ? entry->tunnel_id : "",
             entry->details ? entry->details : "",
             thread_id);
}

/**
 * Write log message to destination
 */
static void write_log(const char *formatted_message)
{
    pthread_mutex_lock(&logger_state.mutex);
    
    switch (logger_state.config.destination) {
        case LOG_DEST_STDOUT:
            printf("%s\n", formatted_message);
            fflush(stdout);
            break;
            
        case LOG_DEST_STDERR:
            fprintf(stderr, "%s\n", formatted_message);
            fflush(stderr);
            break;
            
        case LOG_DEST_FILE:
            if (logger_state.log_file) {
                rotate_log_file();
                if (logger_state.log_file) {
                    fprintf(logger_state.log_file, "%s\n", formatted_message);
                    fflush(logger_state.log_file);
                }
            }
            break;
            
#ifdef HAVE_SYSLOG
        case LOG_DEST_SYSLOG:
            syslog(LOG_INFO, "%s", formatted_message);
            break;
#endif
            
        default:
            break;
    }
    
    pthread_mutex_unlock(&logger_state.mutex);
}

int logger_init(const logger_config_t *config)
{
    if (!config) {
        return -1;
    }
    
    if (logger_state.initialized) {
        logger_cleanup();
    }
    
    // Copy configuration
    memcpy(&logger_state.config, config, sizeof(logger_config_t));
    
    // Initialize mutex
    if (pthread_mutex_init(&logger_state.mutex, NULL) != 0) {
        return -1;
    }
    
    // Open log file if needed
    if (config->destination == LOG_DEST_FILE && config->filename) {
        logger_state.log_file = fopen(config->filename, "a");
        if (!logger_state.log_file) {
            pthread_mutex_destroy(&logger_state.mutex);
            return -1;
        }
    }
    
#ifdef HAVE_SYSLOG
    // Initialize syslog if needed
    if (config->destination == LOG_DEST_SYSLOG) {
        openlog("rdp2tcp", LOG_PID | LOG_CONS, LOG_DAEMON);
    }
#endif
    
    logger_state.initialized = 1;
    
    LOG_INFO(LOG_CAT_GENERAL, "Logger initialized with level %s", 
             level_names[config->level]);
    
    return 0;
}

void logger_cleanup(void)
{
    if (!logger_state.initialized) {
        return;
    }
    
    pthread_mutex_lock(&logger_state.mutex);
    
    if (logger_state.log_file) {
        fclose(logger_state.log_file);
        logger_state.log_file = NULL;
    }
    
#ifdef HAVE_SYSLOG
    if (logger_state.config.destination == LOG_DEST_SYSLOG) {
        closelog();
    }
#endif
    
    pthread_mutex_unlock(&logger_state.mutex);
    pthread_mutex_destroy(&logger_state.mutex);
    
    logger_state.initialized = 0;
}

void logger_set_level(log_level_t level)
{
    if (level < LOG_LEVEL_MAX) {
        logger_state.config.level = level;
    }
}

void logger_set_format(log_format_t format)
{
    if (format < LOG_FORMAT_MAX) {
        logger_state.config.format = format;
    }
}

void log_structured(log_level_t level, log_category_t category,
                   const char *module, const char *function, int line,
                   const char *tunnel_id, const char *details,
                   const char *fmt, ...)
{
    if (!logger_state.initialized || level < logger_state.config.level) {
        return;
    }
    
    char message[1024];
    char formatted[2048];
    va_list args;
    
    va_start(args, fmt);
    vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);
    
    log_entry_t entry = {
        .timestamp = time(NULL),
        .level = level,
        .category = category,
        .module = module,
        .function = function,
        .line = line,
        .message = message,
        .tunnel_id = tunnel_id,
        .details = details
    };
    
    switch (logger_state.config.format) {
        case LOG_FORMAT_TEXT:
            format_text(&entry, formatted, sizeof(formatted));
            break;
        case LOG_FORMAT_JSON:
            format_json(&entry, formatted, sizeof(formatted));
            break;
        case LOG_FORMAT_SYSLOG:
            format_text(&entry, formatted, sizeof(formatted));
            break;
        default:
            return;
    }
    
    write_log(formatted);
}

void log_tunnel(log_level_t level, const char *tunnel_id, const char *fmt, ...)
{
    if (!logger_state.initialized || level < logger_state.config.level) {
        return;
    }
    
    char message[1024];
    va_list args;
    
    va_start(args, fmt);
    vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);
    
    log_structured(level, LOG_CAT_TUNNEL, NULL, NULL, 0, 
                   tunnel_id, NULL, "%s", message);
}

void log_security(log_level_t level, const char *event, const char *source,
                 const char *details, const char *fmt, ...)
{
    if (!logger_state.initialized || level < logger_state.config.level) {
        return;
    }
    
    char message[1024];
    va_list args;
    
    va_start(args, fmt);
    vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);
    
    char full_details[512];
    snprintf(full_details, sizeof(full_details), 
             "event=%s, source=%s, details=%s", 
             event ? event : "", 
             source ? source : "", 
             details ? details : "");
    
    log_structured(level, LOG_CAT_SECURITY, NULL, NULL, 0, 
                   NULL, full_details, "%s", message);
}

void log_performance(const char *metric, double value, const char *unit,
                    const char *tunnel_id)
{
    if (!logger_state.initialized) {
        return;
    }
    
    char details[256];
    snprintf(details, sizeof(details), "metric=%s, value=%.2f, unit=%s",
             metric, value, unit ? unit : "");
    
    log_structured(LOG_LEVEL_INFO, LOG_CAT_PERFORMANCE, NULL, NULL, 0,
                   tunnel_id, details, "Performance metric recorded");
}

void log_audit(const char *user, const char *action, const char *resource,
               const char *result, const char *details)
{
    if (!logger_state.initialized) {
        return;
    }
    
    char audit_details[512];
    snprintf(audit_details, sizeof(audit_details),
             "user=%s, action=%s, resource=%s, result=%s, details=%s",
             user ? user : "",
             action ? action : "",
             resource ? resource : "",
             result ? result : "",
             details ? details : "");
    
    log_structured(LOG_LEVEL_AUDIT, LOG_CAT_SECURITY, NULL, NULL, 0,
                   NULL, audit_details, "Audit event recorded");
}

const char *get_log_level_name(log_level_t level)
{
    if (level < LOG_LEVEL_MAX) {
        return level_names[level];
    }
    return "UNKNOWN";
}

const char *get_log_category_name(log_category_t category)
{
    if (category < LOG_CAT_MAX) {
        return category_names[category];
    }
    return "UNKNOWN";
}
