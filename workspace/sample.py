"""Sample file for the workspace so the context engine has something to retrieve."""

def greet(name: str) -> str:
    """Greets the person passed in"""
    return f"Hello, {name}!"


def hello(name: str) -> str:
    """Greets the person passed in"""
    return f"Hi, {name}!"


def main():
    """Runs the main function"""
    print(hello("world"))
    print(greet("User"))


if __name__ == "__main__":
    main()
