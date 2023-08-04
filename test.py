import sqlite3
import pandas as pd

conn = sqlite3.connect("./data/agents.db")

df = pd.read_sql_query("SELECT * FROM agents", con=conn)

conn.close()

print(df[["agent_id", "name", "phone", "agent_url"]])

# from utils import User

# user = User()

# print(user.fetch_users()[0])