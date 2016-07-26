========
Aiologin
========

This module provides extension to the `aiohttp_session <http://aiohttp-session.
readthedocs.io/en/latest>`_ and `aiohttp.web <https://aiohttp.readthedocs.io/en/
latest/web.html>`_ projects by extending their functionality with this login
management tool. The style of this login management module was greatly inspired
by the flask-login module.

Disclaimer
----------
This module expects that you have a working understanding of the aiohttp and
aiohttp_session modules. Links to the tutorials for those are:
http://aiohttp.readthedocs.io/en/stable/ and
http://aiohttp-session.readthedocs.io/en/latest/. Additionally, this module uses
aiohttp.test_utils which is currently only available in the latest version of
aiohttp.

Installation
------------
To install this module just use pip3 with the following command

.. code:: Python

    sudo pip3 install aiologin

Getting Started
---------------
The first thing you are going to want to do is create your server.py file.
Inside that file you are going to want to define your user class which is needed
store your users session's information. The begging of the server file as well
as the User class should minimally look like this:

.. code:: Python

    #!/usr/bin/python3

    import asyncio
    from urllib.parse import parse_qs

    from aiohttp import web
    from aiohttp_session import session_middleware, SimpleCookieStorage

    import aiologin
    class User(aiologin.AbstractUser):
    def __init__(self, email, password):
        print("user class made")
        self.email = email
        self.password = password

    @property
    def authenticated(self):
        return True

    @property
    def forbidden(self):
        return False
*Note:* The User class should inherit from aiologin.AbstractUser
and define its authenticated and forbidden properties inside the user class. If
these conditions are not met the module with throw Exceptions.

Further Setup, Creating Your Handlers and Authentication Methods 
----------------------------------------------------------------
Once your User class has be created in your server.py file you now should create
your handler and authentication methods that your server will use to handle the 
routes you will add later. See the sample below for some example handler and 
authentication methods. At the very least you should create two handlers one for
a Login route and one for a Logout route.

Additionally, you should define the auth_by_header and auth_by_session methods,
that will be passed into the aiologin class. These two authorization methods
should return a User object. Below are two example authentication methods for
header and session.

.. code:: Python

    async def auth_by_header(request, key):
    print("inside the auth_by_header method")
    if key == '1234567890':
        return TestUser('Test@User.com', 'foobar')
    return None

    async def auth_by_session(request, profile):
    print("inside the auth_by_session method")
    if 'email' in profile and profile['email'] == 'trivigy@gmail.com' and \
            'password' in profile and profile['password'] == 'blueberry':
        return TestUser(profile['email'], profile['password'])
    return None

Furthermore, whatever handlers you want to be secured should have the
@aiologin.secured decorator before it. This will create a wrapper for your
handler that will create a user based on the authentication methods you defined
earlier. Below are the three handlers, one for login and logout, as well as a
one for the home route that is secured so only a logged in user could access it.

.. code:: Python

    @aiologin.secured
    async def handler(request):
        print(await request.aiologin.current_user())
        return web.Response(body=b'OK')

    async def login(request):
        await request.aiologin.login(User())
        return web.Response()

    async def logout(request):
        await request.aiologin.logout()
        return web.Response()

More Setup, Creating Your Web App and Adding Routes To It 
---------------------------------------------------------
Now you need to create your web app that will contain your routes as well as
your middleware that you can add at your own discretion. What you will
definitely need to add is the session_middleware with the SimpleCookieStorage
class passed in. See the example below

.. code:: Python

        app = web.Application(middlewares=[
            session_middleware(SimpleCookieStorage())
        ])
        
Once you defined your web app, add it to the aiologin class via it's setup
method, as well as pointers to your auth_by_header and auth_by_session methods.
See the example below

.. code:: Python

        aiologin.setup(
        app=app,
        auth_by_header=auth_by_header,
        auth_by_session=auth_by_session
    )

One last step before starting your server is to add your routes. For that all
you need to do is manually add your routes with their respective handler
methods.
        

Last Steps, Creating and Starting Your Event Loop
-------------------------------------------------
Once everything is set up, we create our async server via an async method that
will create and run our server for as long as we need. the code for that looks
as follows:

.. code:: Python

    async def init(loop,app):
        srv = await loop.create_server(
            app.make_handler(), '0.0.0.0', 8080)
        return srv

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop,app))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

Signals
-------
Right now the signals are provisional only. To create a signal make a asyncio
function and insert it into aiologin like so

.. code:: Python

    @asyncio.coroutine
    def login_message():
        print("login signal")

    aiologin.on_login.append(login_message)

TODOs
-----
- Extended documentations
- Stale user (required re-login) functionality

License
-------

MIT License
