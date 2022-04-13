import os
import sys
import click

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    # The branch=True option enables branch coverage analysis, which, in
    # addition to tracking which lines of code execute, checks whether for
    # every conditional both the True and False cases have executed. 
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

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
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')
def test(coverage):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))
    
    import unittest
    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


# Source Code Profiling
@app.cli.command()
@click.option('--length', default=25,
              help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None,
              help='Directory where profiler data files are saved.')
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.middleware.profiler import ProfilerMiddleware
    profile_dir and os.makedirs(profile_dir, exist_ok=True)
    app.wsgi_app = ProfilerMiddleware(
        app.wsgi_app, 
        restrictions=[length],
        profile_dir=profile_dir,
        filename_format="{time:.0f}-{method}-{path}-{elapsed:.0f}ms.prof",
    )
    app.run(debug=False)
    
    
if __name__ == '__main__':
    profile()