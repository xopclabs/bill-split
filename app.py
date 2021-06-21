import py_cui
import logging
from backend import Splitter


class SplitterUI:

    def __init__(self, root: py_cui.PyCUI):
        self.root = root
        self.root.set_title('bill-split | People')

        # Widgets for person adding
        self.people_textbox = self.root.add_text_box('Enter a name', 0, 4, column_span=12)
        self.people_scrollmenu = self.root.add_scroll_menu('Group', 1, 4, row_span=3, column_span=12)
        self.people_next = self.root.add_button('Next', 4, 4, column_span=12, command=self.people_next)
        # Adding a shortcut for adding and deleting a person
        self.people_textbox.add_key_command(py_cui.keys.KEY_ENTER, self.people_add_person)
        self.people_scrollmenu.add_key_command(py_cui.keys.KEY_DELETE, self.people_del_person)
        self.people_scrollmenu.add_key_command(py_cui.keys.KEY_D_LOWER, self.people_del_person)

    def people_add_person(self):
        person = str(self.people_textbox.get()).strip()
        if person != '':
            self.people_scrollmenu.add_item(person)
        self.people_textbox.clear()

    def people_del_person(self):
        self.people_scrollmenu.remove_selected_item()

    def people_next(self):
        # Get names
        names = self.people_scrollmenu.get_item_list()
        self.splitter = Splitter(names)
        # Create new widget set for next screen
        self.cart_set = self.root.create_new_widget_set(7, 3 + len(names))
        # Add labels for each name
        self.cart_names_labels = {}
        for i, name in enumerate(self.splitter.names):
            self.cart_names_labels[name] = self.cart_set.add_label(name, 0, 3 + i)
        # Add button for entering items
        self.cart_items_button = self.cart_set.add_button('Add item', 0, 0, column_span=2, command=self.cart_add_item)
        # Add scrollmenus for items, prices and quantities
        self.cart_scrollmenus = {}
        self.cart_scrollmenus['item'] = self.cart_set.add_scroll_menu('Item', 1, 0, row_span=5, column_span=2)
        self.cart_scrollmenus['price'] = self.cart_set.add_scroll_menu('Price', 1, 2, row_span=5, column_span=1)
        for i, name in enumerate(self.splitter.names):
            self.cart_scrollmenus[name] = self.cart_set.add_scroll_menu(name, 1, 3 + i, row_span=5, column_span=1)
        for menu in self.cart_scrollmenus.values():
            menu.add_key_command(py_cui.keys.KEY_DELETE, self.cart_del_item)
            menu.add_key_command(py_cui.keys.KEY_D_LOWER, self.cart_del_item)
            menu.add_key_command(py_cui.keys.KEY_J_LOWER, self.cart_scroll_down)
            menu.add_key_command(py_cui.keys.KEY_K_LOWER, self.cart_scroll_up)
        # Change title
        self.root.set_title('bill-split | Shopping cart')
        # Change screen to shopping cart editing screen
        self.root.apply_widget_set(self.cart_set)

    def cart_add_item(self):
        def add_item(text):
            self.cart_scrollmenus['item'].add_item(text)
            self.cart_scrollmenus['price'].add_item(str(0.0))
            for name in self.splitter.names:
                self.cart_scrollmenus[name].add_item(str(0))

        self.root.show_text_box_popup('Enter new item name (and optionally, price and people buying it)', add_item)

    def cart_del_item(self):
        for menu in self.cart_scrollmenus.values():
            menu.remove_selected_item()

    def cart_scroll_up(self):
        for menu in self.cart_scrollmenus.values():
            menu._scroll_up()

    def cart_scroll_down(self):
        for menu in self.cart_scrollmenus.values():
            viewport_height = menu.get_viewport_height()
            menu._scroll_down(viewport_height)

if __name__ == '__main__':
    root = py_cui.PyCUI(5, 20)
    root.enable_logging(logging_level=logging.DEBUG)
    root.toggle_unicode_borders()
    ui = SplitterUI(root)
    try:
        root.start()
    finally:
        pass
