import os
from dotenv import load_dotenv

load_dotenv()
from groq import Groq
import subprocess


def get_diff():
    print("Git Changes Staged")
    result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError("Current directory is not inside a Git repository.")

    return result.stdout


def generate_commit(diff):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    diff_msg = [
        {
            "role": "system",
            "content": """
            You are a commit writer agent from Git dff. and Give only the commit message don't give extra things
            Here is a example:
                feat: add environment handling and commit‑writer script

                - Add a `.env` file to store the Groq API key (`GROQ_API_KEY`).
                - Create a `.gitignore` entry for the virtual environment (`venv/`).
                - Introduce `app.py`, a small utility that:
                * Loads environment variables via `python‑dotenv`.
                * Stages all current changes and captures the staged diff.
                * Sends the diff to Groq’s LLM (model `openai/gpt‑oss‑120b`) to generate a concise commit message.
                * Prints token usage statistics and the generated commit message.
            """,
        },
        {"role": "user", "content": str(diff)},
    ]

    cmt_msg = client.chat.completions.create(
        messages=diff_msg, model="openai/gpt-oss-120b"
    )

    return (
        cmt_msg.choices[0].message.content,
        cmt_msg.usage.prompt_tokens,
        cmt_msg.usage.completion_tokens,
        cmt_msg.usage.total_tokens,
    )


if __name__ == "__main__":
    result = generate_commit(get_diff())
    cmt_msg = result[0]
    input_token = result[1]
    used_token = result[2]
    total_token = result[3]
    print()
    print("Input Token      :", input_token)
    print("Output Token     :", used_token)
    print("Total Token      :", total_token)
    print("\nCommit Message :", cmt_msg)

    result = subprocess.run(
        ["git", "commit", "-m", cmt_msg], capture_output=True, text=True
    )

    print(result.stdout)
