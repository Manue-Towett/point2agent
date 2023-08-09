import os
from typing import Optional
from datetime import datetime

from sqlalchemy import (
    Column, 
    DateTime, 
    MetaData, 
    String, 
    Boolean,
    Integer,
    Table, 
    create_engine, 
    select
)
from tkinter import StringVar, IntVar

from .logger import Logger
from .data_handler import Agent

class SQLHandler:
    """Creates a  database and manages insertion, deletion and updates"""
    if not os.path.exists('./data/'):
        os.makedirs('./data/')

    logger = Logger("SQLHandler")

    def __init__(self) -> None:
        file_path = os.path.abspath(os.getcwd())+"/data/agents.db"

        self.engine = create_engine('sqlite:///'+file_path, future=True)

        self.table = self.__create_table("agents")

    def __create_table(self, table: str) -> Table:
        """Creates a table to store agent information
           
           :param table_name: the name of the table to be created
        """
        self.logger.info(f"Checking if table <{table}> exists...")

        meta = MetaData()

        agents_table = Table(
            table, meta,
            Column("agent_id", String, primary_key=True),
            Column("name", String),
            Column("location", String),
            Column("agent_url", String),
            Column("website", String),
            Column("phone", String),
            Column("office_phone", String),
            Column("fax_phone", String),
            Column("linkedin", String),
            Column("facebook", String),
            Column("description", String),
            Column("date_scraped", DateTime),
            Column("email_used", String),
            Column("phone_used", String),
            Column("contacted", Boolean)
        )

        meta.create_all(self.engine)

        return agents_table

    def add_agent(self, agent: Agent) -> None:
        """Add a new agent to the database"""
        self.logger.info("Adding new agent to database")

        with self.engine.connect() as connection:
            connection.execute(self.table.insert().values(
                    agent_id = agent.agent_id, 
                    name = agent.name,
                    location = agent.location,
                    agent_url = agent.agent_url,
                    website = agent.website,
                    phone = agent.phone,
                    office_phone = agent.office_phone,
                    fax_phone = agent.fax_phone,
                    linkedin = agent.linkedin,
                    facebook = agent.facebook,
                    description = agent.description,
                    date_scraped = agent.date_scraped,
                    email_used = agent.email_used,
                    phone_used = agent.phone_used,
                    contacted = agent.contacted
                )
            )

            connection.commit()
        
        self.logger.info("Record added successfully")

    def fetch_agent_ids(self) -> list[str]:
        """Fetches all the agent_ids from a given table"""
        self.logger.info(f"Fetching agent ids from table <{self.table}> ...")

        with self.engine.connect() as connection:
            agents = connection.execute(self.table.select()).fetchall()

            [self.delete_agent(agent[0]) for agent in agents if not agent[-1]]

        with self.engine.connect() as connection:
            agent_ids = connection.execute(select(self.table.c.agent_url)).fetchall()
        
        if len(agent_ids):
            agent_ids = [agent_id[0] for agent_id in agent_ids]

            self.logger.info(f"Agents found: {len(agent_ids)}")
        else:
            self.logger.info(f"No agents found")
        
        return agent_ids

    def fetch_agents(self, str_value: StringVar, num_agents: IntVar) -> list:
        """Fetches all the agents from a given table"""
        self.logger.info(f"Fetching agents from table <{self.table}> ...")

        with self.engine.connect() as connection:
            agents = connection.execute(self.table.select()).fetchall()
        
        if len(agents):
            self.logger.info(f"Agents found: {len(agents)}")
        else:
            self.logger.info(f"No agents found")
        
        num_agents.set(len(agents))

        try:
            str_value.set(str(agents[-1][-1]).split(" ")[0])
        except:
            str_value.set(" ")

    def delete_agents(self) -> None:
        """Deletes all the agents from a given table"""
        self.logger.info(f"Deleting all agents from <{self.table}> ...")

        with self.engine.connect() as connection:
            connection.execute(self.table.delete())

            connection.commit()
        
        self.logger.info(f"Deleted all agents from <{self.table}>")
    
    def delete_agent(self, agent_id) -> None:
        """Deletes an agent from a given table"""
        self.logger.info(f"Deleting agent from <{self.table}> ...")

        with self.engine.connect() as connection:
            connection.execute(self.table.delete().where(self.table.c.agent_id == agent_id))

            connection.commit()
        
        self.logger.info(f"Deleted agent from <{self.table}>")
    
    def run(self, agent_details: dict[str, str], update: Optional[bool] = False) -> None:
        """Generates an agent and adds to database"""
        if not update:
            agent_details.update({"contacted": False})

            agent = Agent(**agent_details)

            self.add_agent(agent)
        else:
            with self.engine.connect() as connection:
                connection.execute(self.table.update().values(contacted = True, 
                                                              email_used = agent_details["email_used"],
                                                              phone_used = agent_details["phone_used"]).\
                                   where(self.table.c.agent_id == agent_details["agent_id"]))
                
                connection.commit()

class User:
    """Manages user information"""
    if not os.path.exists('./data/'):os.makedirs('./data/')

    logger = Logger("User")

    def __init__(self) -> None:
        file_path = os.path.abspath(os.getcwd())+"/data/agents.db"

        self.engine = create_engine('sqlite:///'+file_path, future=True)
        self.table = self.__create_table(f"user")
    
    def __create_table(self, table:str) -> Table:
        """Creates a table to store user information
           
           :param table_name: the name of the table to be created
        """
        self.logger.info(f"Checking if table <{table}> exists...")

        meta = MetaData()

        user_table = Table(
            table, meta,
            Column("id", Integer, primary_key=True),
            Column("first_name", String),
            Column("last_name", String),
            Column("api_key", String),
            Column("email", String),
            Column("subject", String),
            Column("message", String),
            Column("zyte_key", String)
        )

        meta.create_all(self.engine)

        return user_table
    
    def add_user(self, data: dict[str, str]) -> None:
        """Add a new user to the database"""
        self.logger.info("Adding new user to database")

        with self.engine.connect() as connection:
            connection.execute(self.table.insert().values(
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    api_key=data["api_key"],
                    email=data["email"],
                    subject=data["subject"],
                    message=data["message"],
                    zyte_key=data["zyte_key"]
                )
            )

            connection.commit()
        
        self.logger.info("Record added successfully")
    
    def delete_users(self) -> None:
        """Deletes all the users from a given table"""
        self.logger.info(f"Deleting all users from <{self.table}> ...")

        with self.engine.connect() as connection:
            connection.execute(self.table.delete())

            connection.commit()
        
        self.logger.info(f"Deleted all users from <{self.table}>")

    def fetch_users(self) -> Optional[list[str]]:
        """Fetches all the users from a given table"""
        self.logger.info(f"Fetching users from table <{self.table}> ...")

        with self.engine.connect() as connection:
            users = connection.execute(self.table.select()).fetchall()
        
        if len(users):
            self.logger.info(f"Users found: {len(users)}")
            return users
        else:
            self.logger.info(f"No users found")
            return []