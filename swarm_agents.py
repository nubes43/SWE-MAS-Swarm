import logging
import os
from swarm import Swarm, Agent
from swarm.repl import run_demo_loop
from swarm_prompts import *
from tools.file_toolkit import extract_function, find_and_replace, list_files_in_repository, list_functions, modify_function, modify_function_args, modify_return_type, read_file, remove_function, write_file
from tools.github_toolkit import analyze_issue, clone_repository, checkout_commit
from tools.executor_toolkit import run_code_execution
from openai import OpenAI
from dotenv import load_dotenv
import pyarrow.parquet as pq
import lunary
import re
import random

load_dotenv()

openai_client=OpenAI()
# lunary.tags_ctx.set(None)
# lunary.tags_ctx.set("SECOND")
# lunary.monitor(openai_client)

client = Swarm(client=openai_client)

def transfer_to_coder():
    """Transfers to Coder Agent"""
    return coder_agent

def transfer_to_file_agent():
    """Transfers to File Agent"""
    return file_agent

def transfer_to_tester():
    """Transfers to Tester Agent"""
    return tester_agent

def transfer_to_triage():
    """Transfers to Triage Agent"""
    return triage_agent

def create_issue_analyzer_agent():
    return Agent(
        name="Issue Analyzer",
        instructions=GITHUB_PROMPT + "When done transfer to Triage. NO USER INPUT NEEDED",
        model="gpt-4o-mini",
        functions=[analyze_issue, clone_repository, checkout_commit, transfer_to_triage],
    )

issue_analyzer_agent = create_issue_analyzer_agent()
triage_agent = Agent(
    name="Triage",
    instructions=TRIAGE_PROMPT,
    model="gpt-4o-mini",
    functions=[transfer_to_file_agent, transfer_to_coder, transfer_to_tester]
)
coder_agent = Agent(
    name="Coder",
    instructions=PROMPT_CODE_GEN + "When done transfer to File Agent. NO USER INPUT NEEDED",
    model="gpt-4o-mini",
    functions=[transfer_to_file_agent]
)

file_agent = Agent(
    name="File",
    instructions=PROMPT_FILE_MANIPULATOR + "When all files are manipulated transfer to Triage and claim TERMINATE. NO USER INPUT NEEDED",
    model="gpt-4o-mini",
    functions=[write_file, modify_function, find_and_replace, read_file, list_files_in_repository, list_functions, extract_function, transfer_to_triage]
)

tester_agent = Agent(
    name= "Tester",
    instructions=CODE_PREP + "When execution was not sucessful. Transfer back to triage. When successfull terminate.",
    model="gpt-4o-mini",
    functions=[write_file, run_code_execution, transfer_to_triage]
)

table = pq.read_table('.\\swebench\\test-00000-of-00001.parquet')

data_dict = table.to_pydict()
columns = data_dict.keys()
rows = [{col: data_dict[col][i] for col in columns} for i in range(len(next(iter(data_dict.values()))))]

random.seed(30)
random.shuffle(rows)

# Enter a number to get any row of SWE-Bench
row = rows[42]
repo = row["repo"]
print(repo)
issue = int(re.search(r'\d+', row["instance_id"]).group())
print(issue)
commit = row["base_commit"]
issue_detail = row["problem_statement"]

# print(response.messages[-1]["content"])

# Paste the console Output to the Chat (Semi-Implement SWE...)
print(f"{repo}/{issue} with base commit {commit} \n ISSUE Description:\n {issue_detail}".replace("\n", " "))

run_demo_loop(client, issue_analyzer_agent, stream=True)
