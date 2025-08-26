from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class ButtonMaker:
    def __init__(self):
        self._button = []
        self._header_button = []
        self._footer_button = []

    def data_button(self, key, data, position=None):
        btn = InlineKeyboardButton(text=key, callback_data=data)
        if not position:
            self._button.append(btn)
        elif position == "header":
            self._header_button.append(btn)
        elif position == "footer":
            self._footer_button.append(btn)

    def url_button(self, key, url, position=None):  # ✅ New method
        btn = InlineKeyboardButton(text=key, url=url)
        if not position:
            self._button.append(btn)
        elif position == "header":
            self._header_button.append(btn)
        elif position == "footer":
            self._footer_button.append(btn)

    def new_row(self):
        self._button.append(None)

    def build_menu(self, b_cols=2, h_cols=8, f_cols=8):
        menu = []
        row = []
        for btn in self._button:
            if btn is None:
                if row:
                    menu.append(row)
                row = []
            else:
                row.append(btn)
                if len(row) == b_cols:
                    menu.append(row)
                    row = []
        if row:
            menu.append(row)
        if self._header_button:
            h_cnt = len(self._header_button)
            if h_cnt > h_cols:
                header_buttons = [self._header_button[i:i + h_cols] for i in range(0, len(self._header_button), h_cols)]
                menu = header_buttons + menu
            else:
                menu.insert(0, self._header_button)
        if self._footer_button:
            f_cnt = len(self._footer_button)
            if f_cnt > f_cols:
                [menu.append(self._footer_button[i:i + f_cols]) for i in range(0, len(self._footer_button), f_cols)]
            else:
                menu.append(self._footer_button)
        return InlineKeyboardMarkup(menu)
      
