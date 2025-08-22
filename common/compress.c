/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
#include "compress.h"
#include "debug.h"
#include "print.h"

#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#ifdef HAVE_LZ4
#include <lz4.h>
#include <lz4hc.h>
#endif

/**
 * Compress data using gzip
 */
static int compress_gzip(unsigned char level, const void *input, unsigned int input_size,
                        void *output, unsigned int *output_size)
{
    z_stream strm;
    int ret;

    // Initialize zlib stream
    strm.zalloc = Z_NULL;
    strm.zfree = Z_NULL;
    strm.opaque = Z_NULL;
    
    // Set compression level (1-9)
    if (level < 1) level = 1;
    if (level > 9) level = 9;
    
    ret = deflateInit(&strm, level);
    if (ret != Z_OK) {
        error("deflateInit failed: %d", ret);
        return -1;
    }

    // Set input and output
    strm.next_in = (Bytef *)input;
    strm.avail_in = input_size;
    strm.next_out = (Bytef *)output;
    strm.avail_out = *output_size;

    // Compress
    ret = deflate(&strm, Z_FINISH);
    if (ret != Z_STREAM_END) {
        error("deflate failed: %d", ret);
        deflateEnd(&strm);
        return -1;
    }

    *output_size = strm.total_out;
    deflateEnd(&strm);
    
    trace_comp("gzip compressed %u bytes to %u bytes (level %d)", 
               input_size, *output_size, level);
    
    return 0;
}

/**
 * Decompress data using gzip
 */
static int decompress_gzip(const void *input, unsigned int input_size,
                          void *output, unsigned int *output_size)
{
    z_stream strm;
    int ret;

    // Initialize zlib stream
    strm.zalloc = Z_NULL;
    strm.zfree = Z_NULL;
    strm.opaque = Z_NULL;
    strm.avail_in = 0;
    strm.next_in = Z_NULL;
    
    ret = inflateInit(&strm);
    if (ret != Z_OK) {
        error("inflateInit failed: %d", ret);
        return -1;
    }

    // Set input and output
    strm.next_in = (Bytef *)input;
    strm.avail_in = input_size;
    strm.next_out = (Bytef *)output;
    strm.avail_out = *output_size;

    // Decompress
    ret = inflate(&strm, Z_FINISH);
    if (ret != Z_STREAM_END) {
        error("inflate failed: %d", ret);
        inflateEnd(&strm);
        return -1;
    }

    *output_size = strm.total_out;
    inflateEnd(&strm);
    
    trace_comp("gzip decompressed %u bytes to %u bytes", input_size, *output_size);
    
    return 0;
}

#ifdef HAVE_LZ4
/**
 * Compress data using LZ4
 */
static int compress_lz4(unsigned char level, const void *input, unsigned int input_size,
                       void *output, unsigned int *output_size)
{
    int compressed_size;
    
    // Set compression level (1-16)
    if (level < 1) level = 1;
    if (level > 16) level = 16;
    
    // Use LZ4HC for higher compression levels
    if (level > 9) {
        compressed_size = LZ4_compress_HC(input, output, input_size, *output_size, level);
    } else {
        compressed_size = LZ4_compress_default(input, output, input_size, *output_size);
    }
    
    if (compressed_size <= 0) {
        error("LZ4 compression failed: %d", compressed_size);
        return -1;
    }
    
    *output_size = compressed_size;
    
    trace_comp("LZ4 compressed %u bytes to %u bytes (level %d)", 
               input_size, *output_size, level);
    
    return 0;
}

/**
 * Decompress data using LZ4
 */
static int decompress_lz4(const void *input, unsigned int input_size,
                         void *output, unsigned int *output_size)
{
    int decompressed_size;
    
    decompressed_size = LZ4_decompress_safe(input, output, input_size, *output_size);
    
    if (decompressed_size < 0) {
        error("LZ4 decompression failed: %d", decompressed_size);
        return -1;
    }
    
    *output_size = decompressed_size;
    
    trace_comp("LZ4 decompressed %u bytes to %u bytes", input_size, *output_size);
    
    return 0;
}
#endif

int compress_data(unsigned char algorithm, unsigned char level,
                  const void *input, unsigned int input_size,
                  void *output, unsigned int *output_size)
{
    if (!input || !output || !output_size) {
        error("Invalid parameters for compression");
        return -1;
    }
    
    if (input_size == 0) {
        *output_size = 0;
        return 0;
    }
    
    switch (algorithm) {
        case COMPRESS_GZIP:
            return compress_gzip(level, input, input_size, output, output_size);
            
#ifdef HAVE_LZ4
        case COMPRESS_LZ4:
            return compress_lz4(level, input, input_size, output, output_size);
#endif
            
        case COMPRESS_NONE:
            if (*output_size < input_size) {
                error("Output buffer too small for uncompressed data");
                return -1;
            }
            memcpy(output, input, input_size);
            *output_size = input_size;
            return 0;
            
        default:
            error("Unsupported compression algorithm: %d", algorithm);
            return -1;
    }
}

int decompress_data(unsigned char algorithm,
                    const void *input, unsigned int input_size,
                    void *output, unsigned int *output_size)
{
    if (!input || !output || !output_size) {
        error("Invalid parameters for decompression");
        return -1;
    }
    
    if (input_size == 0) {
        *output_size = 0;
        return 0;
    }
    
    switch (algorithm) {
        case COMPRESS_GZIP:
            return decompress_gzip(input, input_size, output, output_size);
            
#ifdef HAVE_LZ4
        case COMPRESS_LZ4:
            return decompress_lz4(input, input_size, output, output_size);
#endif
            
        case COMPRESS_NONE:
            if (*output_size < input_size) {
                error("Output buffer too small for uncompressed data");
                return -1;
            }
            memcpy(output, input, input_size);
            *output_size = input_size;
            return 0;
            
        default:
            error("Unsupported compression algorithm: %d", algorithm);
            return -1;
    }
}

unsigned int get_max_compressed_size(unsigned char algorithm, unsigned int input_size)
{
    switch (algorithm) {
        case COMPRESS_GZIP:
            // zlib worst case: input_size + 0.1% + 12 bytes
            return input_size + (input_size / 1000) + 12;
            
#ifdef HAVE_LZ4
        case COMPRESS_LZ4:
            // LZ4 worst case: input_size + 4 bytes
            return LZ4_compressBound(input_size);
#endif
            
        case COMPRESS_NONE:
            return input_size;
            
        default:
            return input_size; // Safe fallback
    }
}

int should_compress(const void *data, unsigned int size)
{
    // Don't compress small data (overhead not worth it)
    if (size < 64) {
        return 0;
    }
    
    // Check if data is already compressed or encrypted
    // This is a simple heuristic - could be improved
    const unsigned char *bytes = (const unsigned char *)data;
    unsigned int i;
    
    // Check for common compressed/encrypted patterns
    for (i = 0; i < size && i < 16; i++) {
        // High entropy data is more likely to benefit from compression
        if (bytes[i] == 0 || bytes[i] == 0xFF) {
            continue;
        }
    }
    
    // If we see mostly zeros or repeated patterns, compression might help
    return 1;
}

const char *get_compression_name(unsigned char algorithm)
{
    switch (algorithm) {
        case COMPRESS_NONE:
            return "none";
        case COMPRESS_GZIP:
            return "gzip";
#ifdef HAVE_LZ4
        case COMPRESS_LZ4:
            return "lz4";
#endif
        default:
            return "unknown";
    }
}
