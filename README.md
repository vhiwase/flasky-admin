# Delete __pycache__ files
```sh
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
```

# Environment Setup
The command that creates a virtual environment has the following structure:
```sh
$ sudo apt-get install python3-venv
$ python3 -m venv venv
```
If you are using Microsoft Windows, make sure you open a command prompt window using the “Run as Administrator” option, and then run this command:
```sh
$ pip install virtualenv
$ virtualenv venv
```
When you want to start using a virtual environment, you have to “activate” it. If you are using a Linux or macOS computer, you can activate the virtual environment with this command:
```sh
$ source venv/bin/activate
```
If you are using Microsoft Windows, the activation command is:
```sh
$ venv\Scripts\activate
```
When you need to build a perfect replica of the virtual environment, you can create a new virtual environment and run the following command on it:
```sh
(venv) $ pip install -r requirements.txt
```
For Linux and macOS, do as follows:
```sh
(venv) $ export FLASK_APP=manage.py
(venv) $ export FLASK_DEBUG=1
```
And for Microsoft Windows:
```sh
(venv) $ set FLASK_APP=manage.py
(venv) $ set FLASK_DEBUG=1
```
When you are done working with the virtual environment, type ```deactivate``` at the command prompt to restore the PATH environment variable for your terminal session and the command prompt to their original states.

---

# Database Setup
Regardless of the source of the database URL, the database tables must be created for the new database. When working with Flask-Migrate to keep track of migrations, database tables can be created or upgraded to the latest revision with a single command:
```sh
(venv) $ flask db upgrade
```
The brute-force solution to update existing database tables to a different schema is to remove the old tables first:

```sh
(venv) $ flask shell
>>> db.drop_all()
>>> db.create_all()
```

Unfortunately, this method has the undesired side effect of destroying all the data in the old database

## Creating a Migration Script
To make changes to your database schema with Flask-Migrate, the following procedure needs to be followed:

- Make the necessary changes to the model classes.
- Create an automatic migration script with the flask db migrate command.
- Review the generated script and adjust it so that it accurately represents the changes that were made to the models.
- Add the migration script to source control.
- Apply the migration to the database with the flask db upgrade command.

The ```flask db migrate``` subcommand creates an automatic migration script:
```sh
(venv) $ flask db migrate -m "initial migration"

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added column 'users.confirmed'
Generating PayslipClassification\migrations\versions\cea46c48c291_initial_migration.py ...  done

```
## Upgrading the Database
Once a migration script has been reviewed and accepted, it can be applied to the database using the flask db upgrade command:
```sh
(venv) $ flask db upgrade

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> cea46c48c291, initial migration
```

# Admin Registration
The insert_roles() function does not directly create new role objects. Instead, it tries to find existing roles by name and update those. A new role object is created only for roles that aren’t in the database already.

Note also that insert_roles() is a static method, a special type of method that does not require an object to be created as it can be invoked directly on the class, for example, as Role.insert_roles().

Let's add the new roles to your development database in a shell session:
```sh
(venv) $ flask shell
>>> db.drop_all()
>>> db.create_all()
>>> Role.insert_roles()
>>> Role.query.all()
[<Role 'Administrator'>, <Role 'User'>, <Role 'Moderator'>]
>>> User.query.all()
[]
>>> user_vaibhav = User(email='vaibhav@example.com', username='vaibhav', password='admin123')
>>> user_vaibhav.role
<Role 'Administrator'>
>>> db.session.add_all([user_vaibhav])
>>> db.session.commit()
>>> User.query.all()
[<User 'vaibhav'>]
```

Let's create some users. Note that default value of APP_ADMIN is set as ```vaibhav@example.com``` on ```config.py``` for development purpose.
```sh
(venv) $ flask shell

>>> user_john = User(email='john@example.com', username='john', password='cat')
```

Although it is not necessary, it is also a good idea to update the user list so that all the user accounts that were created before roles and permissions existed have a role assigned. You can run the following code in a Python shell to perform this update:
```sh
(venv) $ flask shell

>>> admin_role = Role.query.filter_by(name='Administrator').first()
>>> default_role = Role.query.filter_by(default=True).first()
>>> for u in User.query.all():
     if u.role is None:
         if u.email == app.config['APP_ADMIN']:
             u.role = admin_role
         else:
             u.role = default_role

```

Let's check the permissions.
```sh
(venv) $ flask shell

>>> user_vaibhav.role
<Role 'Administrator'>
>>> user_john.role
<Role 'User'>
```

To write the objects to the database, the session needs to be committed by calling its commit() method:
```sh
>>> db.session.add_all([user_john])
>>> db.session.commit()
```

# User Registration
Because no user registration functionality has been built, a new user can only be registered from the shell at this time:
```sh
(venv) $ flask shell

>>> user1 = User(email='user1@example.com', username='username1', password='user1Password')
>>> db.session.add(user1)

>>> user2 = User(email='user2@example.com', username='username2', password='user2Password')
>>> db.session.add(user2)

>>> db.session.commit()
```

# Unit Tests
The unit tests can be executed as follows:
```sh
(venv) $ flask test
```
Code coverage tools measure how much of the application is exercised by unit tests and can provide a detailed report that indicates which parts of the application code are not being tested.
```sh
>>> flask test --coverage
```

# Running the Application
The application as usual:
```sh
(venv) $ flask run
```
The ```--host``` argument is particularly useful because it tells the web server what network interface to listen to for connections from clients. By default, Flask’s development web server listens for connections on localhost, so only connections originating from the computer running the server are accepted. The following command makes the web server listen for connections on the public network interface, enabling other computers in the same network to connect as well:
```sh
(venv) $ flask run --host 0.0.0.0
```
The ```--reload```, ```--no-reload```, ```--debugger```, and ```--no-debugger``` options provide a greater degree of control on top of the debug mode setting.

# Pre-commit
Following command will help to remove trailing-whitespace, check case conflict, check added large files, check merge conflict by using isort, black and flake8 automation tools.
```sh
python3 pre-commit-2.15.0.pyz run  -a
```

# Testing Web Services with HTTPie
To test a web service, an HTTP client must be used. The two most used clients for testing Python web services from the command line are cURL and HTTPie. While both are useful tools, the latter has a much more concise and readable command line syntax that is tailored specifically to API requests.

Assuming the development server is running on the default http://127.0.0.1:5000 address, a GET request can be issued from another terminal window as follows:

```sh
http --json --auth vaibhav@example.com:admin123 GET http://127.0.0.1:5000/api/v1/users/
```
```sh
http --json --auth vaibhav@example.com:admin123 GET http://127.0.0.1:5000/api/v1/users_per_page/
```
```sh
http --json --auth vaibhav@example.com:admin123 GET http://127.0.0.1:5000/api/v1/users_per_page/?page=2
```
```sh
http --json --auth vaibhav@example.com:admin123 GET http://127.0.0.1:5000/api/v1/users/5
```
```sh
http --json --auth vaibhav@example.com:admin123 POST http://127.0.0.1:5000/api/v1/tokens/
```
```sh
http --json --auth eyJhbGciOiJIUzUxMiIsImlhdCI6MTY0OTE4NjY4NiwiZXhwIjoxNjQ5MTkwMjg2fQ.eyJpZCI6Mn0.FU1FX7GTn67e97pRTB78my5xqtu3PXFF8c4KoiYrrB7fzkGvMjUSw8Dy2oSlZnmnzTrzPkIj6K0UJixzY_WXag: GET http://127.0.0.1:5000/api/v1/users/5
```
```sh
http --json --auth eyJhbGciOiJIUzUxMiIsImlhdCI6MTY0OTE4NjY4NiwiZXhwIjoxNjQ5MTkwMjg2fQ.eyJpZCI6Mn0.FU1FX7GTn67e97pRTB78my5xqtu3PXFF8c4KoiYrrB7fzkGvMjUSw8Dy2oSlZnmnzTrzPkIj6K0UJixzY_WXag: GET http://127.0.0.1:5000/api/v1/users/
```
```sh
http --json --auth eyJhbGciOiJIUzUxMiIsImlhdCI6MTY0OTE4NjY4NiwiZXhwIjoxNjQ5MTkwMjg2fQ.eyJpZCI6Mn0.FU1FX7GTn67e97pRTB78my5xqtu3PXFF8c4KoiYrrB7fzkGvMjUSw8Dy2oSlZnmnzTrzPkIj6K0UJixzY_WXag: GET http://127.0.0.1:5000/api/v1/users_per_page/
```
```sh
http --json --auth eyJhbGciOiJIUzUxMiIsImlhdCI6MTY0OTE4NjY4NiwiZXhwIjoxNjQ5MTkwMjg2fQ.eyJpZCI6Mn0.FU1FX7GTn67e97pRTB78my5xqtu3PXFF8c4KoiYrrB7fzkGvMjUSw8Dy2oSlZnmnzTrzPkIj6K0UJixzY_WXag: GET http://127.0.0.1:5000/api/v1/users_per_page/?page=2
```

# Source Code Profiling
Another possible source of performance problems is high CPU consumption, caused by functions that perform heavy computing. Source code profilers are useful in finding the slowest parts of an application. A profiler watches a running application and records the functions that are called and how long each takes to run. It then produces a detailed report showing the slowest functions.

Profiling is typically done only in a development environment. A source code profiler makes the application run much slower than normal, because it has to observe and take notes on all that is happening in real time. Profiling on a production system is not recommended, unless a lightweight profiler specifically designed to run in a production environment is used.

When the application is started with ```flask profile``` which is replaced by ```python manage.py```, the console will show the profiler statistics for each request, which will include the slowest 25 functions. The ```--length``` option can be used to change the number of functions shown in the report. If the ```--profile-dir``` option is given, the profile data for each request is saved to a file in the given directory. The profiler data files can be used to generate more detailed reports that include a call graph. 

Below command is working in older version of [flask](https://github.com/pallets/flask/pull/2781). Some other solutions are [here](https://github.com/pallets/flask/issues/2776)

```sh
(venv) $ flask profile
Warning: Silently ignoring app.run() because the application is run from the flask command line executable.  Consider putting app.run() behind an if __name__ == "__main__" guard to silence this warning.
  app.run(debug=False)
```
Alternatively we can still run as follows

```sh
(venv) $ python manage.py
```
Or with some optional parameters as given below:

```sh
(venv) $ python manage.py --length=25 --profile-dir=profile_dir
```