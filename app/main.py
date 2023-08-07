import re
import time
import random
import itertools
import threading
from queue import Queue
from typing import Optional
from urllib.parse import urlparse

import requests
import pandas as pd
from bs4 import BeautifulSoup
from requests import Response
from tkinter import StringVar, IntVar, Text, END

from utils import Logger, SQLHandler

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Dnt": "1",
    "Origin": "https://www.point2homes.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

PROXIES = {
    "http": "http://77838c23371147dbb9fd5a0df1f04394:@proxy.crawlera.com:8011/",
    "https": "http://77838c23371147dbb9fd5a0df1f04394:@proxy.crawlera.com:8011/"
}

class AgentsScraper:
    """Scrapes agents from https://www.point2homes.com"""
    requests.packages.urllib3.disable_warnings()

    def __init__(self, 
                 links: IntVar, 
                 agents: IntVar, 
                 records: IntVar, 
                 state: StringVar, 
                 log: Text,
                 df: pd.DataFrame,
                 emails: list[str], 
                 close_event: threading.Event) -> None:
        self.logger = Logger(__class__.__name__)
        self.logger.info("*****Point2Agent Bot Started*****")

        self.df = df
        self.state = state
        self.text_log = log
        self.emails = emails
        self.links_var = links
        self.agents_var = agents
        self.records_var = records
        self.close_event = close_event

        self.queue = Queue()
        self.home_queue = Queue()
        self.sql_handler = SQLHandler()
        self.session = requests.Session()

        self.regx = re.compile(r"sitekey'\s+:\s+\S(\w+)\S,", re.DOTALL)
        
        self.agents = []
        self.queued = []
        self.contacted = []

        self.agents_contacted = self.sql_handler.fetch_agent_ids()

        self.records_num = self.records_var.get()

        self.base_url = "https://www.point2homes.com"

    def __request_html(self, 
                       url: str, 
                       headers: Optional[dict[str, str]]) -> Response:
        """Makes an http request to https://www.point2homes.com"""
        for _ in range(4):
            try:
                response = requests.get(url, headers=headers, proxies=PROXIES, verify=False, timeout=5)

                if response.ok:
                    return response
                
            except:pass
    
    @staticmethod
    def __get_soup_element(soup: BeautifulSoup, selector: str, param: Optional[str] = None) -> str|None:
        """Gets an element from the given BeautifulSoup object"""
        try:
            element = soup.select_one(selector)
        except:
            element = None
        
        if element is not None:
            if param is None:
                element = element.get_text(strip=True)
            else:
                element = element[param]
        
        return element
    
    def __extract_agent_urls(self, response: Response) -> list[str]:
        """Extracts links to agents' profiles"""
        soup = BeautifulSoup(response.text, "html.parser")

        agent_profiles = []

        for agent in soup.select("a.ic-profile"):
            agent_profiles.append(agent["href"])
        
        if not len(agent_profiles):
            homes = []

            for home in soup.select("h3.item-address-title > a"):
                homes.append(home["href"])
            
            [self.home_queue.put((home, agent_profiles)) for home in homes]
            self.home_queue.join()
        
        for url, email in zip(agent_profiles, itertools.cycle(self.emails)):
            if not url in self.queued:
                print(email)
                self.queue.put((url, email))

                self.queued.append(url)
            
            self.links_var.set(len(self.queued))

        self.logger.info("Agent links extracted: {}".format(len(set(self.queued))))
    
    def __extract_agent_details(self, response: Response) -> dict[str, str]:
        """Extracts the details for a given agent"""
        soup = BeautifulSoup(response.text, "html.parser")

        agent = {
            "agent_id": "",
            "name": self.__get_soup_element(soup, "h1.agent-name"),
            "location": self.__get_soup_element(soup, "div.agent-location"),
            "agent_url": response.url,
            "website": self.__get_soup_element(soup, "div.website > a", "href"),
            "phone": self.__get_soup_element(
                            soup, "li.phone-cell > span", "data-phone"),
            "office_phone": self.__get_soup_element(
                                soup, "li.phone-office > span", "data-phone"),
            "fax_phone": self.__get_soup_element(
                                soup, "li.phone-fax > span", "data-phone"),
            "linkedin": self.__get_soup_element(soup, "a.linkedin-button", "href"),
            "facebook": self.__get_soup_element(soup, "a.facebook-button", "href")
        }

        description = ""

        for desc in soup.select("div.section-description"):
            description += desc.get_text(strip=True)
        
        agent["description"] = description

        return agent
    
    def __extract_form_details(self, response: Response) -> tuple[dict[str, str], BeautifulSoup]:
        """Extracts form details from the server response"""
        soup = BeautifulSoup(response.text, "html.parser")

        form = soup.select_one("form#agent_form")

        details = {}

        for inp in form.select("input"):
            try:
                details[inp["name"]] = inp["value"]
            except:pass
        
        return details, form
    
    def __submit_message(self, url: str, 
                         details: dict[str, str|int],
                         headers: dict[str, str]) -> None:
        """Submits a message to a given agent"""
        while True:
            try:
                response = self.session.post(url, params=details, headers=headers, proxies=PROXIES, verify=False)

                if response.ok:
                    self.logger.info("Agent contacted successfully.")

                    return response.json()
                
                return {"StatusMessage": "Your inquiry has been sent!"}
                
            except:self.logger.error("")
    
    def __solve_recaptcha(self, sitekey: str, cookies: dict[str, str], url: str, api: str) -> str:
        """Solves the recaptcha on agent page"""
        payload = {
            "key": api,
            "method": "userrecaptcha",
            "googlekey": sitekey,
            "json": 1,
            "cookies": cookies,
            "pageurl": url
        }

        while True:
            try:
                response = requests.post("http://2captcha.com/in.php", data=payload)

                if response.ok:
                    break

            except: pass

            time.sleep(5)

        params = {
            "key": payload["key"],
            "action": "get",
            "id": response.json()["request"],
            "json": 1
        }

        while True:
            time.sleep(15)

            try: 
                response = requests.get("http://2captcha.com/res.php", params=params)
                
                data = response.json()

                if data["request"] != "CAPCHA_NOT_READY":
                    token = data["request"]

                    return token
                
            except:pass
    
    def __process_agent(self, agent_url: str, post_url: str, api_key: str, user: dict[str, str]) -> dict[str, str]:
        """Process an agent i.e. scrape and message the agent"""
        url = self.base_url + agent_url

        self.logger.info("Getting agent details from {}".format(url))

        while not self.close_event.is_set():
            try:
                response = self.session.get(url, headers=HEADERS, proxies=PROXIES, verify=False)

                if self.close_event.is_set():return

                if response.ok:
                    details, form = self.__extract_form_details(response)

                    agent = self.__extract_agent_details(response)

                    agent["agent_id"] = details["agentId"]

                    agent["agent_url"] = url

                    if agent["agent_url"] in self.agents_contacted:
                        return agent
                    
                    agent_lst = [agent]
                    
                    df = pd.concat([self.df, pd.DataFrame(agent_lst)])

                    self.df = df[["agent_id", "name", "phone", "agent_url"]].drop_duplicates().reset_index(drop=True)

                    pd.set_option("display.max_rows", self.df.shape[0] + 1)

                    self.text_log.delete("1.0", END)

                    self.text_log.insert("1.0", self.df)

                    self.sql_handler.run(agent)

                    self.records_num += 1

                    self.records_var.set(self.records_num)

                    sitekey = self.regx.search(str(form)).group(1)

                    cookies = self.session.cookies.get_dict()

                    cookie = ""

                    for key, value in cookies.items():
                        cookie += "{}:{};".format(key, value)
                    
                    self.logger.info("Solving recaptcha for agent >> {}".format(agent["name"]))
                    
                    token = self.__solve_recaptcha(sitekey, cookie, url, api_key)

                    if self.close_event.is_set():return

                    details.update(user)

                    details.update({
                        "g-recaptcha-response": token
                    })

                    headers = {**HEADERS, 
                               "Referer": url,
                               "Content-Type": "x-www-form-urlencoded; charset=UTF-8"}
                    
                    self.logger.info("Contacting agent >> {}".format(agent["name"]))

                    details["FromPhone"] = self.__generate_phone()
                    
                    response = self.__submit_message(post_url, details, headers)

                    if response["StatusMessage"] == "Your inquiry has been sent!":
                        self.agents_no += 1

                        self.agents_var.set(self.agents_no)

                        self.agents_contacted.append(agent["agent_url"])

                        return agent
                    
            except:self.logger.error("")
    
    def __generate_phone(self) -> str:
        """Generates a dummy phone number"""
        fmt = "({}{}{}) {}{}{}-{}{}{}{}"

        numbers = []

        for _ in range(10):
            numbers.append(random.randrange(0, 9))

        phone_no = fmt.format(*numbers)

        return phone_no

    def __work(self, api_key: str, user: dict[str, str]) -> None:
        """Work to be done by the form submitting thread"""
        post_url = self.base_url + "/Email/ContactAgent/"

        self.agents_no = 0

        while not self.close_event.is_set():
            agent_url, email = self.queue.get()

            user["FromEmail"] = email.strip()

            if not self.base_url + agent_url in self.agents_contacted:
                agent = self.__process_agent(agent_url, post_url, api_key, user)

                if agent:
                    self.sql_handler.run(agent, True)
                    
                    self.agents.append(agent)

            self.queue.task_done()
    
    def __work_homes(self) -> None:
        """Work to be done by home threads"""
        while not self.close_event.is_set():
            home_url, links = self.home_queue.get()

            url = self.base_url + home_url

            response = self.__request_html(url, HEADERS)

            soup = BeautifulSoup(response.text, "html.parser")

            try:
                link = soup.select_one("a.ic-profile")["href"]

                if self.base_url + link not in self.agents_contacted \
                    and link not in links and link not in self.queued:
                    links.append(link)

            except:pass

            self.home_queue.task_done()
    
    def scrape(self, start_url: str, api_key: str, user: dict[str, str]) -> None:
        """Entry point to the scraper"""
        [threading.Thread(target=self.__work, daemon=True, args=(api_key, user)).start() for _ in range(10)]

        [threading.Thread(target=self.__work_homes, daemon=True).start() for _ in range(10)]

        page_slug = urlparse(start_url).path

        if "page=" in page_slug:
            page_slug = page_slug.replace("page=", "page={}")
        else:
            page_slug = page_slug + "?page={}"

        page, strike = 1, 0

        while not self.close_event.is_set():
            queue_len = len(set(self.queued))

            url = self.base_url + page_slug.format(page)

            response = self.__request_html(url, HEADERS)

            self.__extract_agent_urls(response)

            if queue_len == len(set(self.queued)):
                strike += 1

                if strike == 15:
                    break

            page += 1

        self.queue.join()

        self.state.set("Finished")

        self.logger.info("Done scraping and contacting agents!")


if __name__ == "__main__":
    p2url = "https://www.point2homes.com/MX/Real-Estate-Agents"

    api = "a8dfbfbbfe30610fbf85e74e84a0ed7f"

    user_d = {
        "FromFirstName": "Kirui",
        "FromLastName": "Towett",
        "FromEmail": "malingukevin23@gmail.com",
        "FromPhone": "(074) 661-0734",
        "Subject": "Need the assistance of an agent",
        "Message": "Hi, I'm following your listings on Point2 and  would appreciate some suggestions related to my searches. Thanks so much!"
    }

    agent_scraper = AgentsScraper()
    agent_scraper.scrape()