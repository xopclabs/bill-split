import py_cui
import logging
from backend import Splitter


class SplitterUI:

    def __init__(self, root: py_cui.PyCUI):
        self.people_root = root
        self.people_root.set_title('bill-split | People')

        # Widgets for person adding
        self.people_textbox = self.people_root.add_text_box('Enter a name', 0, 4, column_span=12)
        self.people_scrollmenu = self.people_root.add_scroll_menu('Group', 1, 4, row_span=3, column_span=12)
        self.people_next = self.people_root.add_button('Next', 4, 4, column_span=12, command=self.people_next)
        # Adding a shortcut for adding and deleting a person
        self.people_textbox.add_key_command(py_cui.keys.KEY_ENTER, self.people_add_person)
        self.people_scrollmenu.add_key_command(py_cui.keys.KEY_DELETE, self.people_del_person)
        self.people_scrollmenu.add_key_command(py_cui.keys.KEY_D_LOWER, self.people_del_person)

    def people_add_person(self):
        self.people_scrollmenu.add_item(
            str(self.people_textbox.get())
        )
        self.people_textbox.clear()

    def people_del_person(self):
        self.people_scrollmenu.remove_selected_item()

    def people_next(self):
        # Get names
        names = self.people_scrollmenu.get_item_list()
        self.splitter = Splitter(names)
        # Create new widget set for next screen
        self.cart_root = self.people_root.create_new_widget_set(5, 3 + len(names))
        # Add labels for each name
        self.cart_names_labels = {}
        for i, name in enumerate(self.splitter.names):
            self.cart_names_labels[name] = self.cart_root.add_label(name, 0, 2 + i)
        # Change title
        self.people_root.set_title('bill-split | Shopping cart')
        # Change screen to shopping cart editing screen
        self.people_root.apply_widget_set(self.cart_root)


if __name__ == '__main__':
    root = py_cui.PyCUI(5, 20)
    root.enable_logging(logging_level=logging.DEBUG)
    root.toggle_unicode_borders()
    ui = SplitterUI(root)
    try:
        root.start()
    finally:
        print(ui.splitter.names)
        print(ui.cart_names_labels)
