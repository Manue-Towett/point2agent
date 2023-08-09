import io
import os
import sys
import sqlite3
import threading
import configparser
from queue import Queue

import pyuac
import pandas as pd
from tkinter import *
from tkinter import filedialog, messagebox

from app import AgentsScraper
from utils import PlaceHolder, SQLHandler, User

CLOSE_EVENT = threading.Event()

HEIGHT, WIDTH = 650, 800

# BUFFER = io.StringIO()
# sys.stderr = BUFFER
# sys.stdout = BUFFER

config = configparser.ConfigParser()

with open("./settings/config.ini", "r") as file:
    config.read_file(file)

COMMAND = config.get("database", "command")

class Point2Bot:
    """Gui for scraping agents and contacting them through contact form"""
    def __init__(self) -> None:
        self.window = Tk()
        self.window.state("zoomed")
        self.window.iconbitmap("./p2c.ico")
        self.window.title("Point2Agent Contact Bot")

        self.window.minsize(WIDTH, HEIGHT)
        # self.window.protocol("WM_DELETE_WINDOW", self.end_session)

        self.sidebar_canvas = Canvas(self.window, bg="white", borderwidth=0, highlightthickness=0)
        self.sidebar_canvas.place(relheight=1, relwidth=0.17)

        self.__create_side_bar()

        self.__create_center_canvas()

        self.user = User()
        self.sql =SQLHandler()
        self.queue = Queue()

        self.scrapper_running = False

    def __create_center_canvas(self) -> None:
        self.center_canvas = Canvas(self.window, bg="white", borderwidth=0, highlightthickness=0)
        self.center_canvas.place(relheight=0.99, relwidth=0.823, relx=0.174, rely=0.005)
    
    def input_fields_setup(self, frame: Frame, input_dict: dict, reveal: bool) -> Entry:
        """
        Sets up the input fields such as the first name and last name
        """
        def resize(e):
            label_size = e.width/23
            label.config(font=("Verdana", int(label_size)))

        label = Label(frame, text=input_dict["text"], bg="white", font=("Verdana", 18))
        label.place(**input_dict["label"])
        label.bind('<Configure>', resize)

        entry = PlaceHolder(frame, input_dict["placeholder"], font="Verdana 12")
        entry.place(**input_dict["entry"])
        
        if not reveal:
            entry.config(show="*")

        return entry
    
    def create_label(self, kwargs: dict) -> None:
        """
        Creates a label with the given keyword arguments
        """
        label = Label(
                    kwargs["frame"],
                    text=kwargs["text"],
                    fg="white",
                    bg="#0057ff",
                    font="Verdana 18 bold italic",
                    anchor=W
                )
        label.place(
            relheight=0.1, relwidth=0.998, relx=0, **kwargs["h"]
        )

    def __create_side_bar(self) -> None:
        """Creates the sidebar"""
        self.create_label({"frame": self.sidebar_canvas,
                           "text": "Point2ContactBot",
                           "h": {"rely": 0}})
        
        def on_enter(e): 
            home_button['background']='#f2f2f2'

        def on_leave(e): 
            home_button['background']='white'

        home_button = Button(self.sidebar_canvas, 
                              text="Home", 
                              font=("Verdana bold", 15), 
                              bg="white", 
                              borderwidth=0, 
                              foreground="#b41e25",
                              command=self.__create_home_window)
        home_button.place(relx=0, rely=0.1, relwidth=0.998, relheight=0.1)

        home_button.bind("<Enter>", on_enter)
        home_button.bind("<Leave>", on_leave)

        line = Label(self.sidebar_canvas, bg="#b41e25")
        line.place(relheight=0.001, relwidth=0.98, rely=0.2, relx=0.01)

        def on_enter_set(e): 
            settings_button['background']='#f2f2f2'

        def on_leave_set(e): 
            settings_button['background']='white'

        settings_button = Button(self.sidebar_canvas, 
                              text="Settings", 
                              font=("Verdana bold", 15), 
                              bg="white", 
                              borderwidth=0, 
                              foreground="#b41e25",
                              command=self.__create_settings_window)
        settings_button.place(relx=0, rely=0.201, relwidth=0.998, relheight=0.1)

        settings_button.bind("<Enter>", on_enter_set)
        settings_button.bind("<Leave>", on_leave_set)

        line = Label(self.sidebar_canvas, bg="#b41e25")
        line.place(relheight=0.001, relwidth=0.98, rely=0.301, relx=0.01)

    def __create_logger(self) -> None:
        """Creates the logger for agent links extracted and agents contacted"""
        global links, agents

        label = Label(self.sidebar_canvas, text="Agent URLS No:", bg="white", font="Verdana 12 italic")
        label.place(relx=0.02, rely=0.8, relheight=0.1, relwidth=0.6)

        underline = Label(self.sidebar_canvas, bg="black", font="Verdana 12")
        underline.place(relheight=0.071, relwidth=0.3, relx=0.615, rely=0.8)

        links = StringVar()
        links.set(0)

        links_label = Label(self.sidebar_canvas, textvariable=links, bg="white", font="Verdana 12")
        links_label.place(relheight=0.07, relwidth=0.3, relx=0.615, rely=0.8)

        label = Label(self.sidebar_canvas, text="Agents Contacted:", bg="white", font="Verdana 12 italic")
        label.place(relx=0.02, rely=0.90, relheight=0.1, relwidth=0.6)

        underline = Label(self.sidebar_canvas, bg="black", font="Verdana 12")
        underline.place(relheight=0.071, relwidth=0.3, relx=0.615, rely=0.90)

        agents = IntVar()
        agents.set(0)

        agents_label = Label(self.sidebar_canvas, textvariable=agents, bg="white", font="Verdana 12")
        agents_label.place(relheight=0.07, relwidth=0.3, relx=0.615, rely=0.90)
    
    def __create_settings_window(self) -> None:
        """Creates the settings window"""
        self.center_canvas.destroy()

        self.__create_center_canvas()

        text = "The following are the required fields for the bot to contact agents:"

        label = Label(self.center_canvas, text=text, fg="#0057ff", bg="white", font="Verdana 18 bold", anchor=W)
        label.place(relheight=0.1, relwidth=0.99, relx=0.05)

        line = Label(self.center_canvas, bg="#0057ff")
        line.place(relheight=0.005, relwidth=0.98, rely=0.1, relx=0.01)

        global first_name, last_name, emails_label, subject, message, api_key, zyte_key

        first_name = self.input_fields_setup(
                    self.center_canvas, {
                        "text":"First Name:",
                        "label": {
                            "relx": 0,
                            "rely": 0.135,
                            "relheight": 0.1,
                            "relwidth": 0.24
                        },
                        "entry": {
                            "relx": 0.21, 
                            "rely": 0.1447,
                            "relwidth": 0.28,
                            "relheight": 0.07
                        },
                        "placeholder": "First Name"
                    },
                    True
                )
        
        last_name = self.input_fields_setup(
                    self.center_canvas, {
                        "text":"Last Name:",
                        "label": {
                            "relx": 0.45,
                            "rely": 0.135,
                            "relheight": 0.1,
                            "relwidth": 0.24
                        },
                        "entry": {
                            "relx": 0.65, 
                            "rely": 0.1447,
                            "relwidth": 0.28,
                            "relheight": 0.07
                        },
                        "placeholder": "Surname"
                    },
                    True
                )
        
        api_key = self.input_fields_setup(
                    self.center_canvas, {
                        "text":"2captcha Key:",
                        "label": {
                            "relx": 0,
                            "rely": 0.235,
                            "relheight": 0.1,
                            "relwidth": 0.24
                        },
                        "entry": {
                            "relx": 0.21, 
                            "rely": 0.2447,
                            "relwidth": 0.28,
                            "relheight": 0.07
                        },
                        "placeholder": "2captcha API Key"
                    },
                    True
                )
        
        zyte_key = self.input_fields_setup(
                    self.center_canvas, {
                        "text":"Zyte API:",
                        "label": {
                            "relx": 0.45,
                            "rely": 0.235,
                            "relheight": 0.1,
                            "relwidth": 0.24
                        },
                        "entry": {
                            "relx": 0.65, 
                            "rely": 0.2447,
                            "relwidth": 0.28,
                            "relheight": 0.07
                        },
                        "placeholder": "Zyte API Key"
                    },
                    True
                )
        
        emails_btn = Button(self.center_canvas, 
                            text="Select Emails File", 
                            bg="#b41e25", 
                            fg="white", 
                            font="Verdana 15", 
                            borderwidth=0,
                            command=self.__select_email)
        emails_btn.place(relx=0.21, rely=0.347, relheight=0.05, relwidth=0.3)

        def resize_emails(e):
            label_size = e.width/23
            label.config(font=("Verdana", int(label_size)))

        emails_label = Label(self.center_canvas, text="", bg="white", font="Verdana 12", anchor=W)
        emails_label.place(relx=0.52, rely=0.345, relheight=0.05, relwidth=0.41)
        emails_label.bind("<Configure>", resize_emails)
        
        subject = self.input_fields_setup(
                    self.center_canvas, {
                        "text":"Email Subject:",
                        "label": {
                            "relx": 0,
                            "rely": 0.435,
                            "relheight": 0.1,
                            "relwidth": 0.24
                        },
                        "entry": {
                            "relx": 0.21, 
                            "rely": 0.4447,
                            "relwidth": 0.72,
                            "relheight": 0.07
                        },
                        "placeholder": "Email subject"
                    },
                    True
                )
        
        def resize(e):
            label_size = e.width/23
            label.config(font=("Verdana", int(label_size)))

        label = Label(self.center_canvas, text="Message:", bg="white", font=("Verdana", 18))
        label.place(relheight=0.1, relwidth=0.24, relx=0, rely=0.535)
        label.bind('<Configure>', resize)

        message = Text(self.center_canvas, bg="#f2f2f2", highlightthickness=0, borderwidth=0, padx=15, pady=15, font="Verdana 12")
        message.place(relx=0.21, rely=0.5447, relheight=0.25, relwidth=0.72)

        global save_button
        
        save_button = Button(self.center_canvas, 
                              text="Save Entries", 
                              font=("Verdana", 15), 
                              bg="#b41e25", 
                              borderwidth=0, 
                              foreground="white", 
                              command=self.__save)
        save_button.place(relx=0.21, rely=0.82, relwidth=0.72, relheight=0.05)

        global error

        error = StringVar()

        error.set("")

        error_label = Label(self.center_canvas, textvariable=error, bg="white", fg="red", font="Verdana 12")
        error_label.place(relx=0.21, rely=0.88, relheight=0.07, relwidth=0.72)
    
    def __select_email(self) -> None:
        """Select emails file"""
        global emails_file

        emails_file = filedialog.askopenfilename(initialdir="/",
                                                 title="Choose a file with emails", 
                                                 filetypes=[("text file", "*.txt")])
        
        emails_label.config(text=emails_file.split("/")[-1])

    def __save(self) -> None:
        """Saves user information to db"""
        f_name = first_name.get()

        if not f_name.strip() or f_name == "First Name":
            error.set("Enter your first name!")

            return
        
        l_name = last_name.get()

        if not l_name.strip() or l_name == "Surname":
            error.set("Enter your surname!")

            return

        apikey = api_key.get()

        if not apikey.strip() or apikey == "2captcha API Key":
            error.set("Enter your 2captcha api key!")

            return
        
        zytekey = zyte_key.get()

        if not zytekey.strip() or zytekey == "Zyte API Key":
            error.set("Enter your Zyte api key!")

            return
        
        try:
            with open(emails_file, "r") as file:
                emails = file.read()
        except:
            error.set("Please select a file with emails!")

            return
        
        subject_str = subject.get()

        if not subject_str.strip() or subject_str == "Email subject":
            error.set("Please enter the email subject!")

            return
        
        message_str = message.get("1.0", END)

        if not message_str.strip():
            error.set("Please enter the message to be sent to agent!")

            return
        
        error.set("")

        self.user.delete_users()

        self.user.add_user({"first_name": f_name, 
                            "last_name": l_name,
                            "email": emails,
                            "api_key": apikey,
                            "subject": subject_str,
                            "message": message_str,
                            "zyte_key": zytekey})
        
        messagebox.showinfo("Success", "Settings updated!")

    def __create_home_window(self) -> None:
        """Creates home window"""
        self.center_canvas.destroy()

        self.__create_center_canvas()

        text = "First, configure settings, then enter start url and click start button"

        global start_url, error_start, records, state, logs_textbox, start_button, state_label

        error_start = StringVar()
        error_start.set("")

        error_label = Label(self.center_canvas, textvariable=error_start, bg="white", fg="red", font="Verdana 12")
        error_label.place(relheight=0.07, relwidth=0.75, relx=0.05, rely=0.945)

        label = Label(self.center_canvas, text=text, fg="#0057ff", bg="white", font="Verdana 18 bold", anchor=W)
        label.place(relheight=0.1, relwidth=0.99, relx=0.05)

        line = Label(self.center_canvas, bg="#0057ff")
        line.place(relheight=0.005, relwidth=0.98, rely=0.1, relx=0.01)

        start_url = PlaceHolder(self.center_canvas, "Enter the start url for the scraper...", font="Verdana 12")
        start_url.place(relheight=0.055, relwidth=0.7, relx=0.05, rely=0.125)

        start_button = Button(self.center_canvas, 
                              text="Start", 
                              font=("Verdana", 15), 
                              bg="#b41e25", 
                              borderwidth=0, 
                              foreground="white",
                              command=self.__start)
        start_button.place(relx=0.75, rely=0.125, relwidth=0.2, relheight=0.055)

        logs_frame = Frame(self.center_canvas, bg="#f2f2f2", borderwidth=0, highlightthickness=0)
        logs_frame.place(relheight=0.755, relwidth=0.9, relx=0.05, rely=0.2)

        scroll_y = Scrollbar(logs_frame, orient="vertical")
        scroll_y.pack(fill="y", side=RIGHT)

        logs_textbox = Text(logs_frame, wrap=WORD, bg="#f2f2f2", yscrollcommand=scroll_y.set, borderwidth=0, highlightthickness=0)
        logs_textbox.place(relheight=0.88, relwidth=0.96, relx=0.05, rely=0.02)

        conn = sqlite3.connect("./data/agents.db")

        df = pd.read_sql_query("SELECT * FROM agents", con=conn)

        conn.close()

        self.df = df[["agent_id", "name", "phone", "agent_url"]]

        if len(df):
            pd.set_option("display.max_rows", df.shape[0] + 1)

            logs_textbox.delete("1.0", END)

            logs_textbox.insert(END, self.df)

        scroll_y.config(command=logs_textbox.yview)

        label = Label(logs_frame, text="Records Found:", bg="#f2f2f2", font="Verdana 12 italic bold")
        label.place(relx=0.01, rely=0.91, relheight=0.1, relwidth=0.15)

        underline = Label(logs_frame, bg="black", font="Verdana 12")
        underline.place(relheight=0.0715, relwidth=0.1, relx=0.15, rely=0.91)

        records = IntVar()
        records.set(len(self.df))

        records_found = Label(logs_frame, textvariable=records, bg="#f2f2f2", font="Verdana 12")
        records_found.place(relheight=0.07, relwidth=0.1, relx=0.15, rely=0.91)

        label = Label(logs_frame, text="State:", bg="#f2f2f2", font="Verdana 12 italic bold")
        label.place(relx=0.24, rely=0.91, relheight=0.1, relwidth=0.15)

        underline = Label(logs_frame, bg="black", font="Verdana 12")
        underline.place(relheight=0.0715, relwidth=0.1, relx=0.35, rely=0.91)

        state = StringVar()
        state.set("idle")

        state_label = Label(logs_frame, textvariable=state, bg="#f2f2f2", font="Verdana 12")
        state_label.place(relheight=0.07, relwidth=0.1, relx=0.35, rely=0.91)

        export_button = Button(logs_frame, 
                              text="Export to Excel", 
                              font=("Verdana", 15), 
                              bg="#b41e25", 
                              borderwidth=0, 
                              foreground="white", 
                              command=self.__export)
        export_button.place(relx=0.52, rely=0.926, relwidth=0.2, relheight=0.05)

        delete_button = Button(logs_frame, 
                              text="Delete Records", 
                              font=("Verdana", 15), 
                              bg="#b41e25", 
                              borderwidth=0, 
                              foreground="white",
                              command=self.__delete)
        delete_button.place(relx=0.726, rely=0.926, relwidth=0.2, relheight=0.05)
    
    def __export(self) -> None:
        """Exports data to csv"""
        directory = filedialog.asksaveasfilename(defaultextension="xlsx", 
                                                 initialdir="/",
                                                 title="Save as",
                                                 filetypes=[("Excel", "*.xlsx")])

        conn = sqlite3.connect("./data/agents.db")

        df = pd.read_sql_query("SELECT * FROM agents", con=conn)

        conn.close()

        df.to_excel(directory, index=False)
    
    def __delete(self) -> None:
        """Deletes the data collected"""
        self.sql.delete_agents()

        logs_textbox.delete("1.0", END)

        records.set(0)
    
    def __start(self) -> None:
        """starts scraping and contacting agents"""
        if self.scrapper_running:
            CLOSE_EVENT.set()

            state_label.config(fg="red")

            state.set("stopped")

            start_button.config(text="Start")

            self.scrapper_running = False

            return
        
        url = start_url.get()

        if not url.strip() or url == "Enter the start url for the scraper...":
            error_start.set("Please enter the start url!")

            return
        
        error_start.set("")

        users = self.user.fetch_users()

        if len(users):
            start_button.config(text="Stop")

            state.set("running")

            state_label.config(fg="green")

            CLOSE_EVENT.clear()

            self.scrapper_running = True

            self.__create_logger()

            user = users[0]

            details = {
                "FromFirstName": user[1],
                "FromLastName": user[2], 
                "FromPhone": "",
                "FromEmail": "",
                "Subject": user[5],
                "Message": user[6]
            }
            
            api_key, emails = user[3], user[4].split("\n")

            zyte_key = user[7]

            agent_scraper = AgentsScraper(links, agents, records, state, logs_textbox, self.df, emails, zyte_key, CLOSE_EVENT)

            threading.Thread(target=agent_scraper.scrape, daemon=True, args=(url, api_key, details)).start()
        
        else:
            error_start.set("Please configure settings first!")

    def run(self) -> None:
        """Entry point to the bot"""
        self.__create_home_window()
        self.window.mainloop()

if __name__ == "__main__": 
    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()
        sys.exit()
    else:
        if COMMAND == "DELETE":
            try:
                os.remove("./data/agents.db")

                config = configparser.ConfigParser()

                config["database"] = {"command": "MAINTAIN"}

                with open("./settings/config.ini", "w") as file:
                    config.write(file)

            except Exception as e: print(e)

        app = Point2Bot()
        app.run()