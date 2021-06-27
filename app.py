import py_cui
import logging
from backend import Splitter
from custom_py_cui import CustomPyCUI


class SplitterUI:
    def __init__(self, root: CustomPyCUI):
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
        # Add cursor line
        self.people_scrollmenu.set_selected_color(py_cui.WHITE_ON_GREEN)

    def people_add_person(self):
        person = str(self.people_textbox.get()).strip()
        # Show error popup if entering duplicate
        if person in self.people_scrollmenu.get_item_list():
            self.root.show_error_popup('Invalid name', 'All names must be unique!')
            self.people_textbox.clear()
            return
        # Validation
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
        self.cart_set = self.root.create_new_custom_widget_set(7, 3 + len(names))

        # Add scrollmenus for items, prices and quantities
        self.cart_scrollmenus = {}
        self.cart_scrollmenus['item'] = self.cart_set.add_linked_scroll_menu('Item', 0, 0, row_span=5, column_span=2)
        self.cart_scrollmenus['price'] = self.cart_set.add_linked_scroll_menu('Price', 0, 2, row_span=5, column_span=1)
        for i, name in enumerate(self.splitter.names):
            self.cart_scrollmenus[name] = self.cart_set.add_linked_scroll_menu(name, 0, 3 + i, row_span=5, column_span=1)
        # Add item hotkey
        self.cart_set.add_key_command(py_cui.keys.KEY_A_LOWER, self.cart_add_item)
        # General settings that apply to every scrollmenu
        for menu in self.cart_scrollmenus.values():
            # Add link between menus
            menu.add_link(list(self.cart_scrollmenus.values()))
            # Hotkeys
            menu.add_key_command(py_cui.keys.KEY_DELETE, menu.remove_selected_item)
            menu.add_key_command(py_cui.keys.KEY_D_LOWER, menu.remove_selected_item)
            menu.add_key_command(py_cui.keys.KEY_C_LOWER, self.cart_change)
            # Coloring
            menu.set_selected_color(py_cui.WHITE_ON_GREEN)

        # Add button perpesenting personal sum for each person
        self.cart_sum_buttons = {}
        for i, name in enumerate(self.splitter.names):
            self.cart_sum_buttons[name] = self.cart_set.add_button(name, 5, 3 + i)

        # Add textbox for each person to enter the amount they paid
        self.cart_paid_textboxes = {}
        for i, name in enumerate(self.splitter.names):
            text = 'Amount paid' if i == 0 else ''
            self.cart_paid_textboxes[name] = self.cart_set.add_text_box(text, 6, 3 + i)

        # Adding global change hotkey
        self.cart_set.add_key_command(py_cui.keys.KEY_A_LOWER, self.cart_add_item)
        self.cart_set.add_key_command(py_cui.keys.KEY_C_LOWER, self.cart_change)
        self.cart_set.add_key_command(py_cui.keys.KEY_D_LOWER, self.cart_del_item)

        self.cart_set.add_key_command(py_cui.keys.KEY_K_LOWER, self.cart_scroll_up)
        self.cart_set.add_key_command(py_cui.keys.KEY_J_LOWER, self.cart_scroll_down)

        # Change title
        self.root.set_title('bill-split | Shopping cart')

        # Change screen to shopping cart editing screen
        self.root.apply_custom_widget_set(self.cart_set)

    def cart_scroll_up(self):
        for menu in self.cart_scrollmenus.values():
            menu._scroll_up()

    def cart_scroll_down(self):
        viewport_height = self.cart_scrollmenus['item'].get_viewport_height()
        for menu in self.cart_scrollmenus.values():
            menu._scroll_down(viewport_height)

    def cart_add_item(self):
        def add_item(text):
            # Parse entries
            parsed_entry = self.parse_entry(text)
            # Add to dataframe
            self.splitter.add_item(parsed_entry)

            self.cart_scrollmenus['item'].add_item(parsed_entry['name'])
            self.cart_scrollmenus['price'].add_item(str(parsed_entry['price']))
            for name in self.splitter.names:
                self.cart_scrollmenus[name].add_item(str(parsed_entry[name]))

        self.root.show_text_box_popup('Enter item name (and optionally, price and people buying it)', add_item)

    def cart_del_item(self):
        widget = self.root.get_selected_widget()
        try:
            if len(widget.get_item_list()) != 0:
                widget.remove_selected_item()
                idx = widget.get_selected_item_index()
                self.splitter.remove_item(idx)
        except Exception as e:
            print(e)

    def cart_change(self):
        def change(text):
            text = text.strip()
            # Updating data in dataframe
            idx = widget.get_selected_item_index()
            row = self.splitter.shopping_cart.iloc[idx].to_dict()
            row[widget.get_title()] = float(text)
            self.splitter.change_item(idx, row)
            # Tinkering with casting for better visual appeal
            if '.' in text:
                text = float(text)
            else:
                text = int(text)
            # Updating data visually
            widget.set_selected_item(text)

        widget = self.root.get_selected_widget()
        try:
            if widget.get_title() == 'Item':
                self.cart_change_item()
            elif widget.get_title() == 'Price':
                self.cart_change_price()
            elif widget.get_title() in self.cart_scrollmenus.keys():
                self.root.show_text_box_popup(f'Change quantity to', change)
        except Exception as e:
            print(e)

    def _change_entry(self, key, text):
        # Getting scrollmenu from dict
        menu = self.cart_scrollmenus[key]
        # Updating data in dataframe
        idx = menu.get_selected_item_index()
        row = self.splitter.shopping_cart.iloc[idx].to_dict()
        if key == 'item':
            if text != '':
                row['name'] = text
            else:
                self.root.show_error_popup('Invalid name', 'Name should not be empty!')
                return
        elif key == 'price':
            try:
                row['price'] = float(text)
            except ValueError:
                self.root.show_error_popup('Invalid price', 'Price should be a number!')
                return
        self.splitter.change_item(idx, row)
        # Updating data visually
        menu.set_selected_item(str(text).strip())

    def cart_change_item(self):
        self.root.show_text_box_popup('Change item name to', lambda text: self._change_entry('item', text))

    def cart_change_price(self):
        self.root.show_text_box_popup('Change item price to', lambda text: self._change_entry('price', text))

    def parse_entry(self, entry):
        # Creating return dictionary
        parsed_entry = {'name': 'Unnamed', 'price': 0.0}
        parsed_entry.update(dict(zip(self.splitter.names,
                                     [0, ]*len(self.splitter.names))))
        # Parsing
        entry = entry.strip().split()
        if entry == []:
            return parsed_entry
        # Finding boundary for item name
        for i, s in enumerate(entry):
            if s[0].isnumeric():
                break
            if i == len(entry) - 1:
                i = -1
        # Adding name to dict
        parsed_entry['name'] = ' '.join(entry[:i])
        # If only name is provided, return
        if i == -1:
            parsed_entry['name'] = ' '.join(entry)
            return parsed_entry
        # Adding price to dict
        parsed_entry['price'] = float(entry[i])
        # Parsing quantites for each person
        for i in range(i + 1, len(entry)):
            # Skipping numbers
            if entry[i][0].isnumeric():
                continue
            # Get person's name
            person = entry[i]
            # Get quantity (default to 1 if not specified)
            if i + 1 < len(entry) and entry[i + 1][0].isnumeric():
                quantity = float(entry[i + 1])
            else:
                quantity = 1
            # Add item to return dict
            parsed_entry[person] = quantity
        return parsed_entry

if __name__ == '__main__':
    root = CustomPyCUI(5, 20)
    root.enable_logging(logging_level=logging.DEBUG)
    root.toggle_unicode_borders()
    ui = SplitterUI(root)
    try:
        root.start()
    finally:
        pass
