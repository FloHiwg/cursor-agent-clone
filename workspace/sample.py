"""Sample file for the workspace so the context engine has something to retrieve."""

def hello(name: str) -> str:
    return f"Hi, {name}!"


def main():
    print(hello("world"))
