import nox_poetry

# Simple function to lint across multiple python versions (to run: nox -s lint)
@nox_poetry.session(python=["3.10", "3.11", "3.12", "3.13"])
def lint(session):
    print(session.python)
    session.run("poetry", "install", "--no-root", external=True)
    session.run("poetry", "run", "ruff", "check", ".", external=True)
