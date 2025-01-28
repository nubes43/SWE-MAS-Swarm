import logging
import os
from swarm import Swarm, Agent
from swarm.repl import run_demo_loop
from swarm_prompts import *
from tools.file_toolkit import manipulate_file
from tools.github_toolkit import analyze_issue, clone_repository, checkout_commit
from tools.executor_toolkit import run_code_execution
from openai import OpenAI
from dotenv import load_dotenv
import lunary
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
    functions=[manipulate_file, transfer_to_triage]
)

tester_agent = Agent(
    name= "Tester",
    instructions=CODE_PREP + "When execution was not sucessful. Transfer back to triage. When successfull terminate.",
    model="gpt-4o-mini",
    functions=[manipulate_file, run_code_execution, transfer_to_triage]
)

# usr_input = input("User: ")
# response = client.run(
#     agent=issue_analyzer_agent,
#     messages=[{"role": "user", "content": f"Issue {usr_input}"}],
#     stream=True
# )

# print(response)

run_demo_loop(client, issue_analyzer_agent, stream=True)
