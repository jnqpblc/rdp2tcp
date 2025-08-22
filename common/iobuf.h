/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2010-2011, Nicolas Collignon
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef __RDP2TCP_IOBUF_H__
#define __RDP2TCP_IOBUF_H__

#include "debug.h"
#include <sys/types.h>

#ifndef IOBUF_MIN_SIZE
#define IOBUF_MIN_SIZE 2048
#endif

/** I/O buffer */
typedef struct iobuf {
	unsigned int size;  /**< used size */
	unsigned int total; /**< allocated size */
	char *data;         /**< data buffer */
#ifdef DEBUG
	const char *name;
	char type;
#endif
} iobuf_t;

#ifdef DEBUG
#define valid_iobuf(x) \
	((x) && (((x)->size <= (x)->total) && ((x)->data || !((x)->total))) \
	 && (x)->name && (((x)->type == 'r') || (x)->type == 'w'))
void iobuf_dump(iobuf_t *);
void __iobuf_init(iobuf_t *, char, const char *);
void __iobuf_init2(iobuf_t *, iobuf_t *, const char *);
#define iobuf_init(buf, type, name) __iobuf_init(buf, type, name)
#define iobuf_init2(buf1, buf2, name) __iobuf_init2(buf1, buf2, name)

#else
#define valid_iobuf(x) \
	((x) && (((x)->size <= (x)->total) && ((x)->data || !((x)->total))))
void __iobuf_init(iobuf_t *);
void __iobuf_init2(iobuf_t *, iobuf_t *);
#define iobuf_init(buf, type, name) __iobuf_init(buf)
#define iobuf_init2(buf1, buf2, name) __iobuf_init2(buf1, buf2)
#endif

#define assert_iobuf(x) assert(valid_iobuf(x))

void iobuf_kill(iobuf_t *);
void iobuf_kill2(iobuf_t *, iobuf_t *);

#if defined(_WIN32) && !defined(__GNUC__)
#define inline __inline
#endif

static inline unsigned int iobuf_datalen(iobuf_t *buf)
{
	return buf->size;
}

static inline void *iobuf_dataptr(iobuf_t *buf)
{
	return buf->size ? buf->data : 0;
}

static inline void *iobuf_allocptr(iobuf_t *buf)
{
	return ((char *)buf->data) + buf->size;
}

/**
 * @brief Consume data from the beginning of an I/O buffer
 * @param[in,out] buf The I/O buffer to consume data from
 * @param[in] consumed Number of bytes to consume
 */
void iobuf_consume(iobuf_t *, unsigned int);

/**
 * @brief Reserve space in an I/O buffer for writing
 * @param[in,out] buf The I/O buffer to reserve space in
 * @param[in] size Number of bytes to reserve
 * @param[out] reserved Pointer to store actual reserved size
 * @return Pointer to reserved memory area, or NULL on failure
 */
void *iobuf_reserve(iobuf_t *, unsigned int, unsigned int *);

/**
 * @brief Commit previously reserved space in an I/O buffer
 * @param[in,out] buf The I/O buffer to commit to
 * @param[in] committed Number of bytes to commit
 */
void iobuf_commit(iobuf_t *, unsigned int);

/**
 * @brief Append data to an I/O buffer
 * @param[in,out] buf The I/O buffer to append to
 * @param[in] data Data to append
 * @param[in] size Size of data to append
 * @return Pointer to appended data, or NULL on failure
 */
void *iobuf_append(iobuf_t *, const void *, unsigned int);
//void iobuf_xfer(iobuf_t *, iobuf_t *);

#endif // __RDP2TCP_IOBUF_H__
// vim: ts=3 sw=3
