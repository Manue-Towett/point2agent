import io
import sys
import threading
from typing import Optional
from datetime import date, datetime
from subprocess import CREATE_NO_WINDOW

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

from utils import PlaceHolder, SQLHandler

HEIGHT, WIDTH = 650, 800
USER = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'

class GoogleFlagger:
    def __init__(self, license: str, uid: str) -> None:
        self.window = Tk()
        self.browser = None
        self.window.state("zoomed")
        self.flagger_running = False
        self.close_event = threading.Event()

        self._license = license
        self.uid = uid

        self.buffer = io.StringIO()
        sys.stdout = self.buffer
        sys.stderr = self.buffer

        self.window.iconbitmap("./G.ico")
        self.window.title("Google Business Profile Flagger")

        self.window.minsize(WIDTH, HEIGHT)
        self.window.protocol("WM_DELETE_WINDOW", self.end_session)

        self.canvas = Canvas(self.window, bg="white")
        self.canvas.place(relheight=1, relwidth=1)

        self.place_title()

        self.combo_style = ttk.Style()

        self.combo_style.theme_create('combo_style', parent='clam', settings={
            'TCombobox':
                {
                    'configure':{
                        'selectbackground':'white',
                        'selectforeground': 'black',
                        'fieldbackground': 'white',
                        'background': '#0057ff',
                        'bordercolor': '#0057ff',
                        'arrowsize': 25,
                        'arrowcolor': 'white'
                    }
                }
            }
        )

        self.combo_style.theme_use("combo_style")

        self.combo_style.layout('TCombobox')

        self.combo_style.element_options("Combobox.padding")

    def end_session(self) -> None:
        threading.Thread(target=self.close_browser).start() 
        self.window.destroy()     

    def close_browser(self) -> None:
        if self.browser:
            self.close_event.set()
            CLOSE_EVENT.set()
    
    def place_title(self) -> None:
        """Configures the title on the GUI"""
        title_frame = Frame(self.canvas, bg="#0057ff")
        title_frame.place(relwidth=1, relheight=0.22)

        self.img = ImageTk.PhotoImage(Image.open("./logo.jpg"))

        def resize_title(e):
            font_size = e.width/28
            title_label.config(font=("Verdana bold italic", int(font_size)))

        title_label = Label(
            title_frame, text="Google Business Profile Flagger",
            font="Verdana 30 bold italic", 
            bg="#0057ff", fg='white')
                            
        title_label.place(relheight=1, relwidth=0.55, relx=0.45)
        title_label.bind("<Configure>", resize_title)

        logo = Label(title_frame, bg="#0057ff", image=self.img)
        logo.place(relx=0.02, relheight=1)
    
    def frame_setup(self, border_args:dict, frame_args:dict={}) -> Frame:
        """
        Sets up a frame on the GUI

        :param border_args: arguments for the border frame
        :param frame_args: arguments for the frame itself
        """
        container_, kwargs = self.canvas, border_args

        if frame_args:
            border_frame = Frame(self.canvas, bg="#0057ff")
            border_frame.place(**border_args)

            container_, kwargs = border_frame, frame_args
        
        frame = Frame(container_, bg="white")
        frame.place(**kwargs)

        return frame
    
    def input_fields_setup(self, frame:Frame, input_dict:dict, 
                           reveal:bool) -> Entry:
        """
        Sets up the input fields such as the username and password
        """
        def resize(e):
            label_size = e.width/10
            label.config(font=("Verdana", int(label_size)))

        label = Label(frame, text=input_dict["text"], bg="white",
                      font=("Verdana", 18))
        label.place(**input_dict["label"])
        label.bind('<Configure>', resize)

        entry = PlaceHolder(frame, input_dict["placeholder"], font="Verdana 12")
        entry.place(**input_dict["entry"])
        
        if not reveal:
            entry.config(show="*")

        return entry
    
    def create_label(self, kwargs:dict) -> None:
        """
        Creates a label with the given keyword arguments
        """
        label = Label(
                    kwargs["frame"],
                    text=kwargs["text"],
                    fg="white",
                    bg="#0057ff",
                    font="Verdana 10",
                    anchor=W
                )
        label.place(
            relheight=0.2, relwidth=1, relx=0, **kwargs["h"]
        )
    
    def login_setup(self) -> None:
        """
        Configures the login pane for the user to be able to 
        enter credentials
        """
        global password, username, no_comment_var

        frame = self.frame_setup(
                    {
                        "relheight":0.72, 
                        "relwidth": 0.34,
                        "relx": 0.65, 
                        "rely": 0.24
                    },
                    {
                        "relheight":0.995, 
                        "relwidth": 0.995,
                        "relx": 0.0025, 
                        "rely": 0.0025
                    }
                )
        
        message_frame = Frame(frame, bg="#0057ff")
        message_frame.place(relheight=0.3, relwidth=1)

        labels = [
            {
                "frame": message_frame, 
                "text": "  ➢ Select the reason",
                "h": {
                    "rely": 0.1
                }
            },
            {
                "frame": message_frame, 
                "text": "  ➢ Select a sorting method",
                "h": {
                    "rely": 0.3
                }
            },
            {
                "frame": message_frame, 
                "text": "  ➢ Enter GBP user credentials",
                "h": {
                    "rely": 0.5
                }
            },
            {
                "frame": message_frame, 
                "text": "  ➢ Click on start button",
                "h": {
                    "rely": 0.7
                }
            },
        ]

        [self.create_label(label) for label in labels]

        username = self.input_fields_setup(
                    frame, {
                        "text":"Username:",
                        "label": {
                            "relx": 0.03,
                            "rely": 0.33,
                            "relheight": 0.1,
                            "relwidth": 0.25
                        },
                        "entry": {
                            "relx": 0.32, 
                            "rely": 0.345,
                            "relwidth": 0.58,
                            "relheight": 0.07
                        },
                        "placeholder": "GBP Username"
                    },
                    True
                )
        
        password = self.input_fields_setup(
                    frame, {
                        "text":"Password:",
                        "label": {
                            "relx": 0.03,
                            "rely": 0.43,
                            "relheight": 0.1,
                            "relwidth": 0.25
                        },
                        "entry": {
                            "relx": 0.32, 
                            "rely": 0.4397,
                            "relwidth": 0.58,
                            "relheight": 0.07
                        },
                        "placeholder": "GBP Password"
                    },
                    False
                )
        
        global start_button
        
        start_button = Button(frame, 
                              text="Start", 
                              font=("Verdana", 15), 
                              bg="#b41e25", 
                              borderwidth=0, 
                              foreground="white", 
                              command=self.check_license)
        start_button.place(relx=0.32, rely=0.62,relwidth=0.58, relheight=0.07)

        def resize_remember(e):
            text_size = e.width/35
            no_comment.config(font=("Verdana italic", int(text_size)))

        no_comment_var = IntVar()

        no_comment = Checkbutton(frame, 
                                 text="Flag no commment reviews", 
                                 variable=no_comment_var, 
                                 onvalue=1, offvalue=0, 
                                 height=5, width=20, 
                                 bg="white", font="Verdana 12")
        no_comment.place(relx=0.16, rely=0.53, relheight=0.07, relwidth=0.8)
        no_comment.bind("<Configure>", resize_remember)

        def on_enter(e): 
            start_button['background']='#a01e10'

        def on_leave(e): 
            start_button['background']='#b41e25'

        start_button.bind("<Enter>", on_enter)
        start_button.bind("<Leave>", on_leave)

        global error_message, pbar_frame

        error_message = StringVar()

        error_message.set(" ")
        label_error_message = Label(frame, 
                                    textvariable=error_message, 
                                    fg="red",
                                    font="Verdana 12 italic",  
                                    bg='white')
        label_error_message.place(relx=0.1, rely=0.70, relwidth=0.9, relheight=0.07)

        pbar_frame = Frame(frame, bg="white")
        pbar_frame.place(rely=0.77, relwidth=1, relheight=0.23)
    
    def left_frame_setup(self) -> None:
        frame = self.frame_setup(
                    {
                        "relheight":0.72, 
                        "relwidth": 0.6,
                        "relx": 0.02, 
                        "rely": 0.24
                    },
                    {}
                )

        selection_frame = Frame(frame, bg="#0057ff")
        selection_frame.place(relheight=0.1, relwidth=1)

        global reason_combo, sort_method_combo, entry_by_company

        reason_combo = self.__configure_combobox(
            {
                "place": {
                    "relx":0.01, "rely":0.1, "relwidth":0.325, "relheight":0.8
                },
                "frame": selection_frame,
                "values":(
                    "   Select reason",
                    "   1. Off topic",
                    "   2. Spam",
                    "   3. Conflict of interest",
                    "   4. Profanity",
                    "   5. Bullying or harassment",
                    "   6. Discrimination",
                    "   7. Personal information"
                )
            }
        )

        def enable(e):
            value = sort_method_combo.current()

            if value == 4:
                entry_by_company.config(state="normal")
                entry_by_company.delete(0, END)

            else: 
                entry_by_company.config(state="disabled")

        sort_method_combo = self.__configure_combobox(
            {
                "place": {
                    "relx":0.345, "rely":0.1, "relwidth":0.325, "relheight":0.8
                },
                "frame": selection_frame,
                "values":(
                    "   Select sorting method",
                    "   1. By Date",
                    "   2. By Most Relevant",
                    "   3. By Lowest Rating",
                    "   4. By Company"
                )
            }
        )

        sort_method_combo.bind("<<ComboboxSelected>>", enable)

        entry_by_company = Entry(
            selection_frame, bg="white", 
            relief=FLAT, font="Verdana 12 italic", bd=5)

        entry_by_company.place(relx=0.68, rely=0.1, relwidth=0.31, relheight=0.8)

        entry_by_company.insert(0, " Enter Company Name")
        entry_by_company.config(state="disabled")
    
    def __configure_combobox(self, args:dict) -> ttk.Combobox:
        combobox = ttk.Combobox(args["frame"], font="Verdana 12", values=args['values'])

        combobox.current(0)

        combobox.option_add("*TCombobox*Listbox*Width", 50)

        combobox.option_add("*TCombobox*Listbox.font", ("Verdana", 12))

        combobox.place(**args['place'])

        return combobox
    
    def __create_pbar_logger(self) -> None:
        """Creates the progress bar, page number and total flagged labels"""
        global label_current_flagged, label_page_value, pbar

        def resize_page_txt(e):
            label_page.config(font=("Verdana italic", int(e.width/12)))

        label_page = Label(pbar_frame, text='Page Number:', font='Verdana 11 italic', bg="white")
        label_page.place(relx=0.05, relheight=0.4, relwidth=0.25)
        label_page.bind("<Configure>", resize_page_txt)

        def resize_page_value(e):
            label_page_value.config(font=("Verdana italic", int(e.width/6)))

        border  = Label(pbar_frame, bg='black')
        label_page_value = Label(pbar_frame, font='Verdana 11 italic', bg="white")

        border.place(relx=0.30, rely=0.1, relheight=0.205, relwidth=0.15)
        label_page_value.place(relx=0.30, rely=0.1, relheight=0.2, relwidth=0.15)
        label_page_value.bind("<Configure>", resize_page_value)

        def resize_total_txt(e):
            label_total.config(font=("Verdana italic", int(e.width/12)))

        label_total = Label(pbar_frame, text='Total Flagged:', font='Verdana 11 italic', bg="white")
        label_total.place(relx=0.46, relheight=0.4, relwidth=0.25)
        label_total.bind("<Configure>", resize_total_txt)

        def resize_total_value(e):
            label_current_flagged.config(font=("Verdana italic", int(e.width/6)))

        border  = Label(pbar_frame, bg='black')
        label_current_flagged = Label(pbar_frame, font='Verdana 11 italic', bg="white")

        border.place(relx=0.71, rely=0.1, relheight=0.205, relwidth=0.15)
        label_current_flagged.place(relx=0.71, rely=0.1, relheight=0.2, relwidth=0.15)
        label_current_flagged.bind("<Configure>", resize_total_value)

        self.combo_style.configure("red.Horizontal.TProgressbar", 
                                   foreground="#b41e25",
                                   background="#b41e25",
                                   troughcolor="white",
                                   bordercolor="white",
                                   lightcolor="#d7dee5",
                                   darkcolor="#d7dee5")

        pbar = ttk.Progressbar(pbar_frame, 
                               style="red.Horizontal.TProgressbar", 
                               mode='determinate', 
                               orient=HORIZONTAL)
        pbar['length'] = pbar_frame.winfo_reqwidth()-2
        pbar.place(rely=0.75, 
                   relwidth=1, 
                   relheight=0.25, 
                   bordermode="outside")
        
        threading.Thread(target=self.set_page, daemon=True).start()
        threading.Thread(target=self.set_flagged, daemon=True).start()
        threading.Thread(target=self.set_bar_value, daemon=True).start()
    
    def __create_boot_logger(self) -> None:
        """Creates a boot logger to inform on the progress of the bot"""
        global boot_status

        def resize_status_txt(e):
            label_status.config(font=("Verdana italic", int(e.width/10)))

        label_status = Label(pbar_frame, text="Status:", font="Verdana 11 italic", bg="white")
        label_status.place(relheight=0.4, relwidth=0.25)
        label_status.bind("<Configure>", resize_status_txt)

        txt = "Initiating flagging subprocess..."

        def resize_boot_txt(e):
            boot_status.config(font=("Verdana italic", int(e.width/28)))

        boot_status = Label(pbar_frame, text=txt, font="Verdana 11 italic", bg="white", fg="green", justify=LEFT, anchor=W)
        boot_status.place(relx=0.25, relheight=0.4, relwidth=0.70)
        boot_status.bind("<Configure>", resize_boot_txt)

        threading.Thread(target=self.update_boot_logger, daemon=True).start()
    
    def __destroy_children(self) -> None:
        """Destroys the children in the pbar frame"""
        for label in pbar_frame.winfo_children():
            label.destroy()
        
    def __create_progress_bar(self, is_boot: Optional[bool]=False) -> None:
        """Creates the progress bar"""
        self.__destroy_children()

        if is_boot:
            self.__create_boot_logger()
        else:
            self.__create_pbar_logger()
        
        threading.Thread(target=self.quit_window, daemon=True).start()
    
    @staticmethod
    def set_page() -> None:
        global PAGE_THREAD

        PAGE_THREAD = True

        while True:
            page = QUEUE_PAGE.get()

            if page is None:
                break

            label_page_value['text'] = page
    
    @staticmethod
    def set_flagged() -> None:
        global FLAGGED_THREAD

        FLAGGED_THREAD = True

        while True:
            flagged = QUEUE_FLAGGED.get()
            
            if flagged is None:
                break

            label_current_flagged['text'] = flagged

    def set_bar_value(self) -> None:
        global BAR_THREAD

        BAR_THREAD = True

        while True:
            value = QUEUE_BAR.get()

            if value is None:
                break

            pbar['value'] = value
            self.window.update_idletasks()

    @staticmethod
    def update_boot_logger() -> None:
        global BOOT_THREAD

        BOOT_THREAD = True

        while True:
            message, color = QUEUE_MESSAGE.get()

            if message is None:
                break

            boot_status["text"] = message

            if color:
                boot_status.config(fg="red")
            else:
                boot_status.config(fg="green")
    
    def quit_window(self) -> None:
        global BOOT_THREAD, BAR_THREAD, FLAGGED_THREAD, PAGE_THREAD

        while True:
            if CLOSE_EVENT.is_set():
                if BOOT_THREAD:
                    QUEUE_MESSAGE.put((None, False))
                    BOOT_THREAD = False

                if BAR_THREAD:
                    QUEUE_BAR.put(None)
                    BAR_THREAD = False
                
                if FLAGGED_THREAD:
                    QUEUE_FLAGGED.put(None)
                    FLAGGED_THREAD = False
                
                if PAGE_THREAD:
                    QUEUE_PAGE.put(None)
                    PAGE_THREAD = False

                return self.__destroy_children()
    
    def click(self) -> None:
        if self.flagger_running:
            self.close_event.set()
            self.flagger_running = False
            start_button["text"] = "Start"
            CLOSE_EVENT.set()
            
            return
        
        user = username.get()
        passw = password.get()
        reason = reason_combo.current()
        sort_method = sort_method_combo.current()
        company = entry_by_company.get()
        no_comment_decision = no_comment_var.get()

        if not user or not passw or user == "GBP Username" or passw == "GBP Password":
            error_message.set("Enter username/password!!!")

        else:
            if reason not in range(1, 8): 
                error_message.set("You have not selected a reason!!!")

            elif sort_method not in range(1, 5):
                error_message.set("You have not selected a sorting method!!!")

            elif sort_method == 4 and not company: 
                error_message.set("You have not entered the company!!!")
            
            else:
                dates = [offtopic.get(), 
                         spam.get(), 
                         personal.get(), 
                         c_interest.get(), 
                         profanity.get(), 
                         bullying.get(), 
                         discrimination.get()]

                error_message.set(" ")
                msg = True
                flagged_recent = False

                for date_ in dates:
                    if date_.strip():

                        if flagged_recent:
                            msg = messagebox.askokcancel(
                                    "GFlagger", 
                                    "You flagged reviews less than 3 days ago. Do you want to continue?"
                                )

                            break

                        try:
                            date_flagged = datetime.strptime(f"{date.today()}", '%Y-%m-%d') - \
                                                            datetime.strptime(date_, '%Y-%m-%d')

                            if int(str(date_flagged).split(" ")[0]) < 3:
                                flagged_recent = True

                        except ValueError:
                                flagged_recent = True
                
                def start_flagger() -> None:
                    str_date, int_reviews = data_dict[reason], num_reviews[reason - 1]

                    if msg:
                        CLOSE_EVENT.clear()
                        self.close_event.clear()

                        self.__create_progress_bar(True)

                        self.flagger_running = True
                        start_button["text"] = "Stop"

                        while self.browser is None:
                            pass

                        if sort_method - 1 !=  3:
                            ReviewFlagger(self.browser, sort_method, reason, 
                                            {
                                                "user": user, 
                                                "password": passw
                                            }, 
                                            no_comment_decision, self.close_event, str_date, int_reviews, total,
                                            self.__create_progress_bar)

                        elif sort_method == 4:
                            CompanyFlagger(self.browser, reason, 
                                            {
                                                "user": user, 
                                                "password": passw
                                            }, 
                                            company,
                                            no_comment_decision, self.close_event, str_date, int_reviews, total,
                                            self.__create_progress_bar)
                
                thread = threading.Thread(target=start_flagger, daemon=True)
                thread.start()

    def logger_frame_setup(self) -> None:
        """Setup logging to show the number of flagged reviews and when they were last flagged"""
        global logger_frame

        logger_frame = self.frame_setup(
            {
                "relheight": 0.62,
                "relwidth": 0.6,
                "relx": 0.02,
                "rely": 0.34
            },
            {}
        )

        logger_frame.config(bg="#d7dee5")

        title_frame = Frame(logger_frame, bg="#d7dee5")
        title_frame.place(relx=0.018, rely=0.02, relwidth=0.8, relheight=0.1)

        title_labels = [
            {
                "frame":title_frame, "text":"Reason", "font":"Verdana 15 bold", "bg":"#d7dee5",
                "place": {
                    "rely":0.12, "relwidth":0.4, "relheight":1, "relx":0
                }
            },
            {
                "frame":title_frame, "text":"Flagged", "font":"Verdana 15 bold", "bg":"#d7dee5",
                "place": {
                    "rely":0.12, "relwidth":0.4, "relheight":1, "relx":0.35
                }
            },
            {
                "frame":title_frame, "text":"Last Flagged", "font":"Verdana 15 bold", "bg":"#d7dee5",
                "place": {
                    "rely":0.12, "relwidth":0.4, "relheight":1, "relx":0.7
                }
            }
        ]

        [self.label_setup(title) for title in title_labels]

        global offtopic, spam, c_interest, discrimination, profanity, bullying, personal

        offtopic = StringVar()
        spam = StringVar()
        c_interest = StringVar()
        discrimination = StringVar()
        profanity = StringVar()
        bullying = StringVar()
        personal = StringVar()

        global offtopic_value, spam_value, c_interest_value, discrimination_value, profanity_value, bullying_value, personal_value

        offtopic_value = IntVar()
        spam_value = IntVar()
        c_interest_value = IntVar()
        discrimination_value = IntVar()
        profanity_value = IntVar()
        bullying_value = IntVar()
        personal_value = IntVar()

        global num_reviews, data_dict, total

        num_reviews = [offtopic_value, 
                       spam_value, 
                       c_interest_value,  
                       profanity_value, 
                       bullying_value, 
                       discrimination_value,
                       personal_value]
        data_dict = {1:offtopic, 
                     2:spam, 
                     3:c_interest, 
                     4:profanity, 
                     5:bullying, 
                     6:discrimination, 
                     7:personal}

        total_reviews = 0

        for (key, str_date), value in zip(data_dict.items(), num_reviews):
            table = SQLHandler(key)

            table.fetch_reviews(str_date, value)

            total_reviews += value.get()

        logs_labels = [
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.13, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "Offtopic",
                "intvar": offtopic_value,
                "txtvar": offtopic
            },
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.22, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "Spam",
                "intvar": spam_value,
                "txtvar": spam
            },
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.31, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "C. of Interest",
                "intvar": c_interest_value,
                "txtvar": c_interest
            },
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.40, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "Profanity",
                "intvar": profanity_value,
                "txtvar": profanity
            },
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.49, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "Bullying",
                "intvar": bullying_value,
                "txtvar": bullying
            },
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.58, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "Discrimination",
                "intvar": discrimination_value,
                "txtvar": discrimination
            },
            {
                "frame": logger_frame,
                "frame_p":{
                    "relx":0.018, "rely":0.65, "relwidth":0.9, "relheight":0.08
                },
                "label_r" : "Personal Info",
                "intvar": personal_value,
                "txtvar": personal
            }
        ]
        
        [self.logs_label_setup(label) for label in logs_labels]

        def resize_total(e):
            flagged_size = e.width/17
            flagged_number_status.config(font=("Verdana bold", int(flagged_size)))

        total = StringVar()
        total.set(str(total_reviews))

        flagged_number = Frame(logger_frame, background="#d7dee5")
        flagged_number.place(relx=0.06, rely=0.84, relwidth=0.47, relheight=0.13)

        flagged_number_status = Label(flagged_number, text="Total Flagged Reviews:",  
                                      bg="#d7dee5", font="Verdana 15 italic")
        flagged_number_status.place(rely=0.12, relwidth=0.5, relheight=1)

        flagged_number_status.bind("<Configure>", resize_total)
        
        def resize_total_num(e):
            flagged_size = e.width/12
            label_flagged_status.config(font=("Verdana italic", int(flagged_size)))

        border_fnumber = Label(flagged_number, background="#003380")
        border_fnumber.place(relx=0.53, relwidth=0.4, relheight=1)

        label_flagged_status = Label(flagged_number, textvariable=total, 
                                     font="Verdana 15 italic",  background="#d7dee5")
        label_flagged_status.place(relx=0.53, relwidth=0.4, relheight=0.97)

        label_flagged_status.bind("<Configure>", resize_total_num)

        def reset_flagged():
            [SQLHandler(i).delete_reviews() for i in range(1, 8)]

            [var.set(" ") for _, var in data_dict.items()]

            [var.set(0) for var in num_reviews]
            
            total.set("0")

        def resize_reset(e):
            flagged_size = e.width/17
            flagged_number_status.config(font=("Verdana bold", int(flagged_size)))

        reset_flagged_frame = Frame(logger_frame, background="#d7dee5")
        reset_flagged_frame.place(relx=0.6, rely=0.87, relwidth=0.47, relheight=0.09)

        reset_button = Button(reset_flagged_frame, text="Delete logs",  bg="#b41e25", 
                              borderwidth=0, foreground="white", font="Verdana 15 italic", 
                              command=reset_flagged)
        reset_button.place(rely=0, relwidth=0.5, relheight=1)

        reset_button.bind("<Configure>", resize_reset)

    def logs_label_setup(self, logs_args:dict) -> Label:
        def resize_reasons(e):
            reason_size = e.width/65
            label_reason.config(font=("Verdana italic", int(reason_size)))

            label_amnt.config(font=("Verdana italic", int(reason_size)))
            
            label_lastrun.config(font=("Verdana italic", int(reason_size)))

        frame = Frame(logs_args["frame"], background="#d7dee5")
        frame.place(**logs_args["frame_p"])

        frame.bind("<Configure>", resize_reasons)

        label_reason = Label(frame, text=logs_args["label_r"], font="Verdana 15 italic", bg="#d7dee5")
        label_reason.place(relx=0.18, rely=0.12, relwidth=0.4, relheight=1, anchor=N)

        label_amnt = Label(frame, textvariable = logs_args["intvar"], font="Verdana 15 italic", 
                           background="#d7dee5")
        label_amnt.place(rely=0.12, relx=0.28, relwidth=0.4, relheight=1)

        label_lastrun = Label(frame, textvariable=logs_args["txtvar"], font="Verdana 15 italic", 
                                       background="#d7dee5")
        label_lastrun.place(rely=0.12, relx=0.56, relwidth=0.5, relheight=1)

    def label_setup(self, label_args:dict) -> None:
        def resize(e):
            label.config(font=("Verdana bold", int(e.width/20)))
            
        label = Label(label_args["frame"], text=label_args["text"], 
                      font=label_args["font"], bg=label_args["bg"])
        label.place(**label_args["place"])

        label.bind("<Configure>", resize)

    def run(self) -> None:
        """Entry point for the GUI"""
        thread = threading.Thread(target=self.__create_browser, daemon=True)
        thread.start()
        thread.join()

        self.login_setup()
        self.left_frame_setup()
        self.logger_frame_setup()
        self.window.mainloop()