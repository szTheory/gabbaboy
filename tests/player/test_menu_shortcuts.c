/* Phase 18 plan 06, research assumption A2 as a machine check: the macOS main menu SDL creates must not bind
 * Command-S, Command-L or Command-Z. If it did, Cocoa would consume those chords as menu key equivalents before the
 * SDL key event reached the player, and the slot keys (D-21) would silently do nothing.
 *
 * The scan walks [[NSApplication sharedApplication] mainMenu] recursively through the Objective-C runtime (this is a
 * plain C file; objc_msgSend is cast to each exact signature) and fails with `menu-shortcut-conflict <key>` when an
 * item's key equivalent is `s`, `l` or `z` with the Command modifier alone.
 *
 * `--seed-conflict` first adds an NSMenuItem with key equivalent `s` (Command is a new item's default modifier) to
 * the main menu's first submenu. That is the control: the scan must then report the conflict and exit 1, which shows
 * the scanner can see the thing it forbids.
 *
 * Usage: test_menu_shortcuts [--seed-conflict] */
#include <SDL3/SDL.h>

#include <objc/message.h>
#include <objc/runtime.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

/* NSEventModifierFlag values (device-independent bits). */
#define MOD_SHIFT (1ul << 17)
#define MOD_CONTROL (1ul << 18)
#define MOD_OPTION (1ul << 19)
#define MOD_COMMAND (1ul << 20)

extern void *objc_autoreleasePoolPush(void);
extern void objc_autoreleasePoolPop(void *pool);

static id send_id(id receiver, const char *selector) {
    return ((id (*)(id, SEL))objc_msgSend)(receiver, sel_registerName(selector));
}

static unsigned long send_ulong(id receiver, const char *selector) {
    return ((unsigned long (*)(id, SEL))objc_msgSend)(receiver, sel_registerName(selector));
}

static id send_id_index(id receiver, const char *selector, unsigned long index) {
    return ((id (*)(id, SEL, unsigned long))objc_msgSend)(receiver, sel_registerName(selector), index);
}

static id send_id_id(id receiver, const char *selector, id argument) {
    return ((id (*)(id, SEL, id))objc_msgSend)(receiver, sel_registerName(selector), argument);
}

static const char *send_cstring(id receiver, const char *selector) {
    return ((const char *(*)(id, SEL))objc_msgSend)(receiver, sel_registerName(selector));
}

static id ns_string(const char *text) {
    return ((id (*)(id, SEL, const char *))objc_msgSend)((id)objc_getClass("NSString"),
                                                         sel_registerName("stringWithUTF8String:"), text);
}

/* Counts every item below `menu` and returns false at the first Command-only s, l or z. */
static bool scan_menu(id menu, unsigned *items, char *conflict) {
    if (menu == NULL) return true;
    const unsigned long count = send_ulong(menu, "numberOfItems");
    for (unsigned long index = 0; index < count; ++index) {
        id item = send_id_index(menu, "itemAtIndex:", index);
        if (item == NULL) continue;
        ++*items;
        const char *key = send_cstring(send_id(item, "keyEquivalent"), "UTF8String");
        const unsigned long mask = send_ulong(item, "keyEquivalentModifierMask") &
                                   (MOD_SHIFT | MOD_CONTROL | MOD_OPTION | MOD_COMMAND);
        if (key != NULL && mask == MOD_COMMAND &&
            (strcmp(key, "s") == 0 || strcmp(key, "l") == 0 || strcmp(key, "z") == 0)) {
            *conflict = key[0];
            return false;
        }
        if (!scan_menu(send_id(item, "submenu"), items, conflict)) return false;
    }
    return true;
}

int main(int argc, char **argv) {
    const bool seed_conflict = argc == 2 && strcmp(argv[1], "--seed-conflict") == 0;
    if (argc > 2 || (argc == 2 && !seed_conflict)) {
        fputs("usage: test_menu_shortcuts [--seed-conflict]\n", stderr);
        return 2;
    }
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        fprintf(stderr, "menu-shortcuts blocked: SDL_Init(SDL_INIT_VIDEO) failed: %s\n", SDL_GetError());
        return 3;
    }
    SDL_Window *window = SDL_CreateWindow("menu-shortcuts", 160, 144, SDL_WINDOW_HIDDEN);
    if (window == NULL) {
        fprintf(stderr, "menu-shortcuts blocked: SDL_CreateWindow failed: %s\n", SDL_GetError());
        SDL_Quit();
        return 3;
    }
    SDL_PumpEvents();

    void *pool = objc_autoreleasePoolPush();
    int code = 0;
    id application = send_id((id)objc_getClass("NSApplication"), "sharedApplication");
    id main_menu = application != NULL ? send_id(application, "mainMenu") : NULL;
    if (main_menu == NULL || send_ulong(main_menu, "numberOfItems") == 0ul) {
        fputs("menu-shortcuts blocked: the SDL main menu does not exist\n", stderr);
        code = 3;
    } else {
        if (seed_conflict) {
            id first = send_id(send_id_index(main_menu, "itemAtIndex:", 0ul), "submenu");
            id alloc = send_id((id)objc_getClass("NSMenuItem"), "alloc");
            id item = ((id (*)(id, SEL, id, SEL, id))objc_msgSend)(alloc, sel_registerName("initWithTitle:action:keyEquivalent:"),
                                                                    ns_string("Seeded conflict"), (SEL)NULL,
                                                                    ns_string("s"));
            if (first == NULL || item == NULL) {
                fputs("menu-shortcuts blocked: could not seed the control item\n", stderr);
                code = 3;
            } else {
                (void)send_id_id(first, "addItem:", item);
            }
        }
        unsigned items = 0u;
        char conflict = '\0';
        if (code == 0) {
            if (!scan_menu(main_menu, &items, &conflict)) {
                printf("menu-shortcut-conflict %c\n", conflict);
                code = 1;
            } else if (items == 0u) {
                fputs("menu-shortcuts blocked: the scan saw no menu items\n", stderr);
                code = 3;
            } else {
                printf("menu-shortcuts pass items=%u\n", items);
            }
        }
    }
    objc_autoreleasePoolPop(pool);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return code;
}
