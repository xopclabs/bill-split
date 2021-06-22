import py_cui
from py_cui.widgets import ScrollMenu
import shutil


class CustomPyCUI(py_cui.PyCUI):
    def __init__(self, arg1, arg2):
        super(CustomPyCUI, self).__init__(arg1, arg2)

    def add_linked_scroll_menu(self, title, row, column, row_span=1, column_span=1, padx=1, pady=0):
        id = 'Widget{}'.format(len(self.widgets.keys()))
        new_scrollmenu = LinkedScrollMenu(id, title,  self.grid, row, column, row_span, column_span, padx, pady, book)
        self.widgets[id] = new_scrollmenu
        if self.selected_widget is None:
            self.set_selected_widget(id)
        return new_scrollmenu

    def apply_custom_widget_set(self, new_widget_set):
        if isinstance(new_widget_set, CustomWidgetSet):
            self.lose_focus()
            self._widgets = new_widget_set._widgets
            self._grid = new_widget_set._grid
            self._keybindings = new_widget_set._keybindings

            if self._simulated_terminal is None:
                if self._stdscr is None:
                    term_size = shutil.get_terminal_size()
                    height = term_size.lines
                    width = term_size.columns
                else:
                    # Use curses termsize when possible to fix resize bug on windows.
                    height, width = self._stdscr.getmaxyx()
            else:
                height = self._simulated_terminal[0]
                width = self._simulated_terminal[1]

            height = height - 4

            self._refresh_height_width(height, width)
            if self._stdscr is not None:
                self._initialize_widget_renderer()
            self._selected_widget = new_widget_set._selected_widget
        else:
            raise TypeError('Argument must be of type CustomWidgetSet')

    def create_new_custom_widget_set(self, num_rows, num_cols):
        return CustomWidgetSet(
            num_rows, num_cols,
            self._logger,
            simulated_terminal=self._simulated_terminal
        )

class CustomWidgetSet(py_cui.widget_set.WidgetSet):
    def __init__(self, num_rows, num_cols, logger, simulated_terminal=None):
        self._widgets = {}
        self._keybindings = {}
        self._simulated_terminal = simulated_terminal
        if self._simulated_terminal is None:
            term_size = shutil.get_terminal_size()
            height = term_size.lines
            width = term_size.columns
        else:
            height = self._simulated_terminal[0]
            width = self._simulated_terminal[1]
        self._height = height
        self._width = width
        self._height = self._height - 4
        self._grid = py_cui.grid.Grid(num_rows, num_cols, self._height, self._width, logger)
        self._selected_widget = None
        self._logger = logger

    def add_linked_scroll_menu(self, title, row, column, row_span=1, column_span=1, padx=1, pady=0):
        id = 'Widget{}'.format(len(self._widgets.keys()))
        new_scrollmenu = LinkedScrollMenu(id, title,  self._grid, row, column, row_span, column_span, padx, pady, self._logger)
        self._widgets[id] = new_scrollmenu
        if self._selected_widget is None:
            self.set_selected_widget(id)
        return new_scrollmenu

    def get_selected_widget(self):
        if self._selected_widget is not None and self._selected_widget in self.get_widgets().keys():
            return self.get_widgets()[self._selected_widget]
        else:
            self._logger.warn('Selected widget ID is None or invalid')
            return None

class LinkedScrollMenu(py_cui.widgets.ScrollMenu):
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady, logger):
        super(LinkedScrollMenu, self).__init__(id, title, grid, row, column, row_span, column_span, padx, pady, logger)
        self.links = []
        self.navkeys = py_cui.keys.ARROW_KEYS + [py_cui.keys.KEY_J_LOWER, py_cui.keys.KEY_K_LOWER]

    def get_title(self):
        return self._title

    def add_link(self, menus):
        self.links = menus


    def _handle_key_press(self, key_pressed):
        def _handle_vim_arrows(menu, key_pressed):
            if key_pressed == py_cui.keys.KEY_J_LOWER:
                viewport_height = menu.get_viewport_height()
                menu._scroll_down(viewport_height)
            elif key_pressed == py_cui.keys.KEY_K_LOWER:
                menu._scroll_up()

        py_cui.widgets.ScrollMenu._handle_key_press(self, key_pressed)
        _handle_vim_arrows(self, key_pressed)
        for menu in self.links:
            # Skip self
            if menu == self:
                continue
            # If navkeys pressed, translate motion to linked menus
            if key_pressed in self.navkeys:
                py_cui.widgets.ScrollMenu._handle_key_press(menu, key_pressed)
                _handle_vim_arrows(menu, key_pressed)

    def _handle_mouse_press(self, x, y):
        for menu in self.links:
            py_cui.widgets.ScrollMenu._handle_mouse_press(menu, x, y)
