import os

from flask_migrate import Migrate

from app import create_app, db
from app.models import Permission, Role, User

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    """
    The shell context processor function returns a dictionary that includes the database
    instance and the models. The flask shell command will import these items
    automatically into the shell, in addition to app, which is imported by default.
    """
    return dict(db=db, User=User, Role=Role, Permission=Permission)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)
