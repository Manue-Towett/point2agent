import dataclasses
from datetime import datetime

@dataclasses.dataclass
class Agent:
    agent_id: str
    name: str
    location: str
    agent_url: str
    website: str
    phone: str
    office_phone: str
    fax_phone: str
    linkedin: str
    facebook: str
    description: str
    email_used: str
    phone_used: str
    contacted: bool
    date_scraped: datetime = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        return f"{self.agent_id} {self.name} -> {self.website}"