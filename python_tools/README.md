# Python Tools

Community tools consists of several python packages to provide APIs and tools for working with ThoughtSpot 
programatically.  

These projects are:
* [DDL Tools](https://github.com/thoughtspot/user_tools/tree/master/ddl_tools): Tools for working with ThoughtSpot DDL.
* [User Tools](https://github.com/thoughtspot/user_tools/tree/master/user_tools): Tools for working with ThoughtSpot users.
* [PyTQL](https://github.com/thoughtspot/user_tools/tree/master/py-tql):  Tools for working with ThoughtSpot Query Language.

### Environment

These tools have all been written in Python 3.x and expect to be run in a 3.6 environment at a minimum.  This section 
describes how to set up a virtual environment to use for the user tools and how to generally install those tools.  

You can either install directly into an existing Python environment, but it's better to run in an virtual environment 
to avoid conflicts with dependencies.  Note that this installation process requires external access to install packages 
and get the Python modules from GitHub.

#### Creating Virtual Environment
To create a virtual environment, you can run the following from the command prompt:

`$ virtualenv -p python3 ./venv`

Note that the `venv` folder can be whatever name and location you like (preferably external to a code repository).

Next, you need to activate the environment with the command: 

`$ source ./venv/bin/activate`

Note that you will need to reactivate the environment whenever you want to use it.  

You should see your prompt change to (venv) plus whatever it was before.  To verify the python version run:

`$ python --version`  You want to be on version 3.6 or higher.

If you want to leave the virtual environment, simple enter `$ deactivate` or close the terminal you are using.

See https://virtualenv.pypa.io/en/latest/ for more details on using virtualenv.

### Downloading and installing the Python Tools

Now that you have an environment for installing into you can install directly from GitHub with the command:

`$ pip install git+https://github.com/thoughtspot/tool_name`.  "tool_name" is the name of the specific tool.

You should see output as the Python tool and dependencies are installed.  

If you want or need to update to a newer version of the Python tool, use the command:

`$ pip install --upgrade git+https://github.com/thoughtspot/tool_name`.  
