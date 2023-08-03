import re
import time
import threading
from queue import Queue
from typing import Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup
from requests import Response

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

class AgentsScraper:
    """Scrapes agents from https://www.point2homes.com"""
    def __init__(self) -> None:
        self.logger = Logger(__class__.__name__)
        self.logger.info("*****Point2Agent Bot Started*****")

        self.queue = Queue()
        self.sql_handler = SQLHandler()
        self.session = requests.Session()

        self.regx = re.compile(r"sitekey'\s+:\s+\S(\w+)\S,", re.DOTALL)
        
        self.agents = []
        self.contacted = []
        self.queued = []

        self.agents_contacted = self.sql_handler.fetch_agent_ids()

        self.base_url = "https://www.point2homes.com"

    def __request_html(self, 
                       url: str, 
                       headers: Optional[dict[str, str]]) -> Response:
        """Makes an http request to https://www.point2homes.com"""
        while True:
            try:
                response = requests.get(url, headers=headers)

                if response.ok:
                    return response
                
            except:pass
    
    @staticmethod
    def __get_soup_element(soup: BeautifulSoup, 
                           selector: str, 
                           param: Optional[str] = None) -> str|None:
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
        
        for url in agent_profiles:
            if not url in self.queued:
                self.queue.put(url)

                self.queued.append(url)

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
                response = self.session.post(url, 
                                             params=details, 
                                             headers=headers)
                
                if response.ok:
                    return response.json()
                
            except:pass
    
    def __solve_recaptcha(self, sitekey: str, cookies: dict[str, str], url: str) -> str:
        """Solves the recaptcha on agent page"""
        payload = {
            "key": "a8dfbfbbfe30610fbf85e74e84a0ed7f",
            "method": "userrecaptcha",
            "googlekey": sitekey,
            "json": 1,
            "cookies": cookies,
            "pageurl": url
        }

        while True:
            try:
                response = requests.post("http://2captcha.com/in.php", 
                                         data=payload)

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
                response = requests.get("http://2captcha.com/res.php", 
                                        params=params)
                
                data = response.json()

                if data["request"] != "CAPCHA_NOT_READY":
                    token = data["request"]

                    return token
                
            except:pass
    
    def __process_agent(self, agent_url: str, post_url: str) -> dict[str, str]:
        """Process an agent i.e. scrape and message the agent"""
        url = self.base_url + agent_url

        self.logger.info("Getting agent details from {}".format(url))

        while True:
            try:
                response = self.session.get(url, headers=HEADERS)

                if response.ok:
                    details, form = self.__extract_form_details(response)

                    agent = self.__extract_agent_details(response)

                    agent["agent_id"] = details["agentId"]

                    agent["agent_url"] = url

                    if agent["agent_id"] in self.agents_contacted:
                        return agent

                    self.sql_handler.run(agent)

                    sitekey = self.regx.search(str(form)).group(1)

                    cookies = self.session.cookies.get_dict()

                    cookie = ""

                    for key, value in cookies.items():
                        cookie += "{}:{};".format(key, value)
                    
                    self.logger.info("Solving recaptcha for agent >> {}".format(agent["name"]))
                    
                    token = self.__solve_recaptcha(sitekey, cookie, url)

                    details.update({
                        "FromFirstName": "Kirui",
                        "FromLastName": "Towett",
                        "FromEmail": "malingukevin23@gmail.com",
                        "FromPhone": "(074) 661-0734",
                        "Subject": "Need the assistance of an agent",
                        "Message": "Hi, I'm following your listings on Point2 and  would appreciate some suggestions related to my searches. Thanks so much!",
                        "g-recaptcha-response": token
                    })

                    headers = {**HEADERS, 
                               "Referer": url,
                               "Content-Type": "x-www-form-urlencoded; charset=UTF-8"}
                    
                    self.logger.info("Contacting agent >> {}".format(agent["name"]))
                    
                    response = self.__submit_message(post_url, details, headers)

                    if response["StatusMessage"] == "Your inquiry has been sent!":
                        self.agents_contacted.append(agent["agent_id"])

                        return agent
                    
            except:pass

    def __work(self) -> None:
        """Work to be done by the form submitting thread"""
        post_url = self.base_url + "/Email/ContactAgent/"

        while True:
            agent_url = self.queue.get()

            agent = self.__process_agent(agent_url, post_url)

            self.sql_handler.run(agent, True)
            
            self.agents.append(agent)

            self.queue.task_done()
    
    def scrape(self) -> None:
        """Entry point to the scraper"""
        threading.Thread(target=self.__work, daemon=True).start()

        page_slug = "/MX/Real-Estate-Agents?page={}"

        page = 1

        while True:
            queue_len = len(set(self.queued))

            url = self.base_url + page_slug.format(page)

            response = self.__request_html(url, HEADERS)

            self.__extract_agent_urls(response)

            if queue_len == len(set(self.queued)):
                break

            page += 1

        self.queue.join()

        self.logger.info("Done scraping and contacting agents!")


if __name__ == "__main__":
    agent_scraper = AgentsScraper()
    agent_scraper.scrape()