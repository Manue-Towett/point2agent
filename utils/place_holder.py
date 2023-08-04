from tkinter import Entry, Misc, FLAT, END

class PlaceHolder(Entry):
    def __init__(self, 
                 master: Misc | None = ..., 
                 placeholder: str = "", 
                 font: str = "Verdana 10", 
                 relief: str = FLAT, 
                 bg: str = "#f2f2f2") -> None:
        super().__init__(master)

        self['font'] = font
        self['relief'] = relief
        self['bg'] = bg

        self['bd'] = 15

        self["highlightthickness"] = 0

        self.placeholder = placeholder

        self.bind("<FocusIn>", self.focus_on)
        self.bind("<FocusOut>", self.focus_off)

        self.insert_placeholder()

    def focus_on(self, *args) -> None:
        if self["fg"] == "grey":
            self.delete(0, END)
            self["fg"] = "black"

    def focus_off(self, *args) -> None:
        if not self.get():
            self.insert_placeholder()
    
    def insert_placeholder(self) -> None:
        self.insert(0, self.placeholder)
        self["fg"] = "grey"