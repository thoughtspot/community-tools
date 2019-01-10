from setuptools import setup, find_packages

setup(name='user_management',
      version='0.1',
      description='This package contains all the user management functionality in ThoughtSpot',
      url='/Users/nikhita.chandra/Desktop/Cetera2',
      # Need to fix url - Git URL
      author='Nikhita Chandra',
      author_email='nikhita.chandra@thoughtspot.com',
      license='MIT',
      packages=['user_management','user_management/user_mgmt'],
      zip_safe=False
      )
