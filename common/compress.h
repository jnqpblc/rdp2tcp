/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
#ifndef __RDP2TCP_COMPRESS_H__
#define __RDP2TCP_COMPRESS_H__

#include "rdp2tcp.h"

/**
 * Compress data using the specified algorithm
 * @param[in] algorithm Compression algorithm (COMPRESS_GZIP, COMPRESS_LZ4)
 * @param[in] level Compression level (1-9 for gzip, 1-16 for lz4)
 * @param[in] input Input data buffer
 * @param[in] input_size Size of input data
 * @param[out] output Output buffer for compressed data
 * @param[in,out] output_size Size of output buffer (updated with actual size)
 * @return 0 on success, negative value on error
 */
int compress_data(unsigned char algorithm, unsigned char level,
                  const void *input, unsigned int input_size,
                  void *output, unsigned int *output_size);

/**
 * Decompress data using the specified algorithm
 * @param[in] algorithm Compression algorithm (COMPRESS_GZIP, COMPRESS_LZ4)
 * @param[in] input Input compressed data buffer
 * @param[in] input_size Size of input data
 * @param[out] output Output buffer for decompressed data
 * @param[in,out] output_size Size of output buffer (updated with actual size)
 * @return 0 on success, negative value on error
 */
int decompress_data(unsigned char algorithm,
                    const void *input, unsigned int input_size,
                    void *output, unsigned int *output_size);

/**
 * Get the maximum compressed size for given input size and algorithm
 * @param[in] algorithm Compression algorithm
 * @param[in] input_size Size of input data
 * @return Maximum compressed size
 */
unsigned int get_max_compressed_size(unsigned char algorithm, unsigned int input_size);

/**
 * Check if compression would be beneficial for given data
 * @param[in] data Input data buffer
 * @param[in] size Size of data
 * @return 1 if compression would be beneficial, 0 otherwise
 */
int should_compress(const void *data, unsigned int size);

/**
 * Get compression algorithm name
 * @param[in] algorithm Compression algorithm
 * @return Algorithm name string
 */
const char *get_compression_name(unsigned char algorithm);

#endif // __RDP2TCP_COMPRESS_H__
