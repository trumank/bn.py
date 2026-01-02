/*
 * Test binary for bn.py Binary Ninja helper script
 * Compile with: gcc -g -o test_binary test_binary.c
 *
 * This binary contains various constructs to test all bn.py features:
 * - Multiple functions with calls between them (disasm, hlil, mlil, callers, callees)
 * - Named and unnamed functions (funcs --named)
 * - Cross-references (xrefs)
 * - Strings (strings)
 * - Global variables and structures (vars, struct, type)
 * - Pointer tables (deref)
 * - Areas suitable for patching (patch)
 * - Comment-worthy locations (comment)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* ========== Structures for testing struct command ========== */

typedef struct {
    int32_t x;
    int32_t y;
    int32_t z;
} Point3D;

typedef struct {
    char name[32];
    uint32_t id;
    uint32_t flags;
    Point3D position;
} Entity;

typedef struct {
    uint8_t magic[4];
    uint32_t version;
    uint32_t entry_count;
    uint64_t data_offset;
    Entity *entities;
} FileHeader;

typedef struct {
    void (*init)(void);
    void (*process)(int);
    void (*cleanup)(void);
    const char *name;
} PluginInterface;

/* ========== Global variables for testing vars command ========== */

const char *g_application_name = "BNTestBinary";
const char *g_version_string = "1.0.0-test";
const char *g_author = "Claude Test Generator";

int g_global_counter = 0;
uint32_t g_flags = 0xDEADBEEF;
Entity g_main_entity = {
    .name = "MainEntity",
    .id = 42,
    .flags = 0x1234,
    .position = {10, 20, 30}
};

FileHeader g_file_header = {
    .magic = {'T', 'E', 'S', 'T'},
    .version = 1,
    .entry_count = 0,
    .data_offset = 0x1000,
    .entities = NULL
};

/* ========== String table for testing strings command ========== */

const char *g_string_table[] = {
    "Error: invalid input",
    "Warning: operation failed",
    "Success: operation completed",
    "Debug: entering function",
    "Critical: memory allocation failed",
    "Info: processing item %d of %d",
    "/etc/config/settings.conf",
    "SELECT * FROM users WHERE id = ?",
    "Authorization: Bearer %s",
    "https://api.example.com/v1/data",
    NULL
};

/* ========== Function pointer table for testing deref command ========== */

void plugin_init(void);
void plugin_process(int value);
void plugin_cleanup(void);

PluginInterface g_plugin = {
    .init = plugin_init,
    .process = plugin_process,
    .cleanup = plugin_cleanup,
    .name = "TestPlugin"
};

/* Pointer array for deref testing */
void *g_pointer_table[8] = {NULL};

/* ========== Helper functions (for callers/callees testing) ========== */

int helper_add(int a, int b) {
    return a + b;
}

int helper_multiply(int a, int b) {
    return a * b;
}

int helper_subtract(int a, int b) {
    return a - b;
}

void helper_print_number(int n) {
    printf("Number: %d\n", n);
}

void helper_print_string(const char *s) {
    if (s) {
        printf("String: %s\n", s);
    }
}

/* ========== Computation functions (for HLIL/MLIL testing) ========== */

int compute_factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * compute_factorial(n - 1);
}

int compute_fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;

    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

int compute_gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

/* ========== Complex function with multiple paths (for xrefs testing) ========== */

int process_command(int cmd, int arg1, int arg2) {
    int result = 0;

    switch (cmd) {
        case 0:
            result = helper_add(arg1, arg2);
            break;
        case 1:
            result = helper_subtract(arg1, arg2);
            break;
        case 2:
            result = helper_multiply(arg1, arg2);
            break;
        case 3:
            result = compute_factorial(arg1);
            break;
        case 4:
            result = compute_fibonacci(arg1);
            break;
        case 5:
            result = compute_gcd(arg1, arg2);
            break;
        default:
            printf("Unknown command: %d\n", cmd);
            result = -1;
    }

    g_global_counter++;
    return result;
}

/* ========== Plugin interface functions ========== */

void plugin_init(void) {
    printf("Plugin initializing: %s\n", g_plugin.name);
    g_flags = 0x1;
}

void plugin_process(int value) {
    printf("Plugin processing value: %d\n", value);
    int result = compute_fibonacci(value % 20);
    helper_print_number(result);
}

void plugin_cleanup(void) {
    printf("Plugin cleanup\n");
    g_flags = 0;
    g_global_counter = 0;
}

/* ========== Entity management functions ========== */

Entity *create_entity(const char *name, uint32_t id) {
    Entity *e = (Entity *)malloc(sizeof(Entity));
    if (!e) {
        printf("Critical: memory allocation failed\n");
        return NULL;
    }

    strncpy(e->name, name, sizeof(e->name) - 1);
    e->name[sizeof(e->name) - 1] = '\0';
    e->id = id;
    e->flags = 0;
    e->position.x = 0;
    e->position.y = 0;
    e->position.z = 0;

    return e;
}

void update_entity_position(Entity *e, int x, int y, int z) {
    if (!e) return;

    e->position.x = x;
    e->position.y = y;
    e->position.z = z;

    printf("Entity %s moved to (%d, %d, %d)\n",
           e->name, e->position.x, e->position.y, e->position.z);
}

void destroy_entity(Entity *e) {
    if (e) {
        printf("Destroying entity: %s (id=%u)\n", e->name, e->id);
        free(e);
    }
}

/* ========== File handling functions ========== */

int validate_header(FileHeader *hdr) {
    if (!hdr) return 0;

    if (hdr->magic[0] != 'T' || hdr->magic[1] != 'E' ||
        hdr->magic[2] != 'S' || hdr->magic[3] != 'T') {
        printf("Error: invalid magic\n");
        return 0;
    }

    if (hdr->version != 1) {
        printf("Warning: unsupported version %u\n", hdr->version);
        return 0;
    }

    return 1;
}

int process_file(const char *filename) {
    printf("Processing file: %s\n", filename);

    if (!validate_header(&g_file_header)) {
        return -1;
    }

    printf("File has %u entries at offset 0x%lx\n",
           g_file_header.entry_count, g_file_header.data_offset);

    return 0;
}

/* ========== Function with inline assembly (platform specific) ========== */

#ifdef __x86_64__
uint64_t get_timestamp(void) {
    uint32_t lo, hi;
    __asm__ volatile ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}
#else
uint64_t get_timestamp(void) {
    return 0;
}
#endif

/* ========== Bitwise operations (good for disasm viewing) ========== */

uint32_t rotate_left(uint32_t value, int bits) {
    return (value << bits) | (value >> (32 - bits));
}

uint32_t rotate_right(uint32_t value, int bits) {
    return (value >> bits) | (value << (32 - bits));
}

uint32_t bitfield_extract(uint32_t value, int start, int length) {
    uint32_t mask = ((1u << length) - 1) << start;
    return (value & mask) >> start;
}

uint32_t bitfield_insert(uint32_t dest, uint32_t src, int start, int length) {
    uint32_t mask = ((1u << length) - 1) << start;
    dest &= ~mask;
    dest |= (src << start) & mask;
    return dest;
}

/* ========== Array/buffer operations ========== */

void fill_buffer(uint8_t *buf, size_t size, uint8_t pattern) {
    for (size_t i = 0; i < size; i++) {
        buf[i] = pattern;
    }
}

int compare_buffers(const uint8_t *a, const uint8_t *b, size_t size) {
    for (size_t i = 0; i < size; i++) {
        if (a[i] != b[i]) {
            return (int)i + 1;
        }
    }
    return 0;
}

void xor_buffers(uint8_t *dest, const uint8_t *src, size_t size) {
    for (size_t i = 0; i < size; i++) {
        dest[i] ^= src[i];
    }
}

/* ========== Initialization function ========== */

void initialize_globals(void) {
    g_global_counter = 0;
    g_flags = 0;

    /* Setup pointer table for deref testing */
    g_pointer_table[0] = (void *)g_application_name;
    g_pointer_table[1] = (void *)g_version_string;
    g_pointer_table[2] = (void *)&g_main_entity;
    g_pointer_table[3] = (void *)&g_file_header;
    g_pointer_table[4] = (void *)plugin_init;
    g_pointer_table[5] = (void *)plugin_process;
    g_pointer_table[6] = (void *)plugin_cleanup;
    g_pointer_table[7] = (void *)g_string_table;

    printf("Globals initialized\n");
}

/* ========== Main entry point ========== */

int main(int argc, char *argv[]) {
    printf("=== %s v%s ===\n", g_application_name, g_version_string);
    printf("Author: %s\n\n", g_author);

    initialize_globals();

    /* Test plugin interface */
    g_plugin.init();
    g_plugin.process(10);

    /* Test computations */
    printf("\nComputation tests:\n");
    printf("Factorial(5) = %d\n", compute_factorial(5));
    printf("Fibonacci(10) = %d\n", compute_fibonacci(10));
    printf("GCD(48, 18) = %d\n", compute_gcd(48, 18));

    /* Test commands */
    printf("\nCommand tests:\n");
    for (int i = 0; i < 6; i++) {
        int result = process_command(i, 10, 5);
        printf("Command %d result: %d\n", i, result);
    }

    /* Test entity management */
    printf("\nEntity tests:\n");
    Entity *e = create_entity("TestEntity", 100);
    if (e) {
        update_entity_position(e, 100, 200, 300);
        destroy_entity(e);
    }

    /* Test bitwise operations */
    printf("\nBitwise tests:\n");
    printf("rotate_left(0x12345678, 8) = 0x%08x\n", rotate_left(0x12345678, 8));
    printf("rotate_right(0x12345678, 8) = 0x%08x\n", rotate_right(0x12345678, 8));
    printf("bitfield_extract(0xABCD1234, 8, 8) = 0x%02x\n", bitfield_extract(0xABCD1234, 8, 8));

    /* Test file processing */
    printf("\nFile tests:\n");
    process_file("/etc/config/settings.conf");

    /* Cleanup */
    g_plugin.cleanup();

    printf("\n=== Tests complete ===\n");
    printf("Global counter: %d\n", g_global_counter);

    return 0;
}
