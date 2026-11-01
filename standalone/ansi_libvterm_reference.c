/* Linux-only independent reference adapter, never linked into a DOS product.
 * libvterm owns parsing, state, scrolling and cells. This file only projects
 * supported ASCII/16-color cell fields into the same VGA file representation.
 */
#include <stdio.h>
#include <stdlib.h>
#include <vterm.h>

static void require(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

static unsigned color(const VTermColor *value)
{
    static const unsigned vga[8] = {0, 4, 2, 6, 1, 5, 3, 7};
    require(VTERM_COLOR_IS_INDEXED(value), "RGB color outside reference projection");
    require(value->indexed.idx < 16, "Palette outside reference projection");
    return vga[value->indexed.idx & 7] | (value->indexed.idx & 8);
}

int main(int argc, char **argv)
{
    VTerm *terminal;
    VTermState *state;
    VTermScreen *screen;
    VTermColor foreground, background;
    VTermPos position;
    FILE *input, *output;
    int byte, row, column;
    require(argc == 3, "usage: ansi-libvterm-reference INPUT CELLS");
    VTERM_CHECK_VERSION;
    terminal = vterm_new(24, 80);
    require(terminal != NULL, "vterm_new failed");
    vterm_set_utf8(terminal, 0);
    state = vterm_obtain_state(terminal);
    screen = vterm_obtain_screen(terminal);
    vterm_color_indexed(&foreground, 7);
    vterm_color_indexed(&background, 0);
    vterm_state_set_default_colors(state, &foreground, &background);
    vterm_state_set_bold_highbright(state, 0);
    vterm_screen_reset(screen, 1);
    input = fopen(argv[1], "rb");
    require(input != NULL, "cannot open input");
    while ((byte = fgetc(input)) != EOF) {
        char value = (char)byte;
        require(byte < 128, "ASCII-only reference; high CP437 bytes require another adapter");
        require(vterm_input_write(terminal, &value, 1) == 1, "input not consumed");
    }
    require(!ferror(input) && fclose(input) == 0, "input read failed");
    vterm_screen_flush_damage(screen);
    output = fopen(argv[2], "wbx");
    require(output != NULL, "cannot exclusively create cell output");
    for (row = 0; row < 24; ++row) {
        for (column = 0; column < 80; ++column) {
            VTermScreenCell cell = {0};
            unsigned fg, bg, attribute, glyph;
            int i;
            position.row = row;
            position.col = column;
            require(vterm_screen_get_cell(screen, position, &cell), "missing cell");
            require(cell.width == 1, "non-unit character width");
            require(!cell.attrs.underline && !cell.attrs.italic && !cell.attrs.conceal &&
                !cell.attrs.strike && !cell.attrs.font && !cell.attrs.dwl &&
                !cell.attrs.dhl && !cell.attrs.small && !cell.attrs.baseline,
                "unsupported cell attributes");
            for (i = 1; i < VTERM_MAX_CHARS_PER_CELL; ++i)
                require(cell.chars[i] == 0, "combining characters unsupported");
            glyph = cell.chars[0] ? cell.chars[0] : ' ';
            require(glyph >= 32 && glyph < 127, "non-ASCII cell");
            fg = color(&cell.fg);
            bg = color(&cell.bg);
            if (cell.attrs.reverse) {
                unsigned temporary = fg;
                fg = bg;
                bg = temporary;
            }
            require(bg < 8, "bright background needs separate VGA blink-mode policy");
            attribute = fg | (bg << 4) | (cell.attrs.bold ? 8 : 0) |
                (cell.attrs.blink ? 128 : 0);
            require(fputc((int)glyph, output) != EOF &&
                fputc((int)attribute, output) != EOF, "cell write failed");
        }
    }
    require(fclose(output) == 0, "cell close failed");
    vterm_state_get_cursorpos(state, &position);
    printf("{\"cursor\":[%d,%d],\"version\":\"%d.%d.%d\"}\n",
        position.row + 1, position.col + 1,
        VTERM_VERSION_MAJOR, VTERM_VERSION_MINOR, VTERM_VERSION_PATCH);
    vterm_free(terminal);
    return 0;
}
