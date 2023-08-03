import dataclasses
from datetime import date

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
    date_scraped: date
    contacted: bool

    def __str__(self) -> str:
        return f"{self.agent_id} {self.name} -> {self.website}"