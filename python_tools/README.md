# Python Tools

Community tools consists of several Python packages that provide APIs and tools for working with ThoughtSpot 
programmatically.  

These projects are:
* [DDL Tools](https://github.com/thoughtspot/ddl_tools): Tools for working with ThoughtSpot DDL.
* [User Tools](https://github.com/thoughtspot/user_tools): Tools for working with ThoughtSpot users.
* [PyTQL](https://github.com/thoughtspot/py-tql):  Tools for working with ThoughtSpot Query Language.

### Environment

These tools have all been written in Python 3.x and expect to be run in a 3.6 environment at a minimum.  This section 
describes how to set up a virtual environment to use for the user tools and how to generally install those tools.  

You can install directly into an existing Python environment, but it's better to run in an virtual environment 
to avoid dependency conflicts.  Note that this installation process requires external access to install packages 
and get the Python modules from GitHub.

#### Creating Virtual Environment

To create a virtual environment, you can run the following from the command prompt:

`$ virtualenv -p python3 ./venv`

Note that the `venv` folder can be whatever name and location you like (preferably external to a code repository). 
It's recommended that you put this into a sub-folder where you can put a few more helper scripts (see below).  For
example, you can create a `tstools` folder on your system, create the virtual environment there and then install the
scripts into that environment.

Next, you need to activate the environment with the command: 

`$ source ./venv/bin/activate`

Note that you will need to reactivate the environment whenever you want to use it.  

You should see your prompt change to (venv) plus whatever it was before.  To verify the python version run:

`$ python --version`  You want to be on version 3.6 or higher.  Note that in some installs you have to use 
`python3` instead of `python`.

If you want to leave the virtual environment, simple enter `$ deactivate` or close the terminal you are using.

See https://virtualenv.pypa.io/en/latest/ for more details on using virtualenv.

### Downloading and installing the Python Tools

Now that you have an environment for installing into you can install directly from GitHub with the command:

`$ pip install git+https://github.com/thoughtspot/tool_name`.  "tool_name" is the name of the specific tool.

You should see output as the Python tool and dependencies are installed.  

If you want or need to update to a newer version of the Python tool, use the command:

`$ pip install --upgrade git+https://github.com/thoughtspot/tool_name`.  

## Reusable Scripts

There are two reusable scripts to assist with setting up and using the environment.  Once you have created
the virtual environment, you can install the scripts and use them instead of manually installing the packages.  

* `upgrade_all` is a script that will install and/or upgrade all of the TS Python tools.  Simply update the 
path in the `TOOLS_DIR` variable and run the script.
* `tstools` is a script that will activate the virtual environment and then provide simpler aliases to run the 
command-line tools. 

If you are using bash, you can create an alias in your .bash_profile to quickly activate the Python environment from 
any location:  `alias tst='source /Users/bill.back/ThoughtSpot/tstools/tstools'`  Then you can simply type `tst`
and the environment and aliases will be available.  Type `deactivate` to exit the virtual environment.

