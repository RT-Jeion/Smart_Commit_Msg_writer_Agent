import os
from dotenv import load_dotenv

load_dotenv()
from groq import Groq
import subprocess


def get_diff():
    staging = subprocess.run(["git", "add", "."])
    print("Git Changes Staged")
    result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError("Current directory is not inside a Git repository.")

    return result.stdout


system_prompt = """
You generate Git commit messages from a provided `git diff`.

Rules:

* Use Conventional Commits: `type: description`
* Types: feat, fix, refactor, perf, test, docs, style, chore, build, ci
* Infer the main purpose of the changes.
* Use imperative mood.
* Keep it concise, ideally under 72 characters.
* Don't invent details.
* Return ONLY the commit message. No explanation, quotes, or markdown.

Example:
`feat: add user authentication`
`fix: handle empty API responses`
`refactor: simplify database connection`

"""


def generate_commit(diff):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    diff_msg = [
        {
            "role": "system",
            "content": system_prompt,
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
