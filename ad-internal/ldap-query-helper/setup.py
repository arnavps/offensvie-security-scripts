from setuptools import setup

setup(name='ldap-simple-search',
      version='0.1.2',
      description='Easily perform simple LDAP queries',
      url='http://github.com/chaordic/python-ldap-simple-search',
      author='Raphael P. Ribeiro',
      author_email='raphael.ribeiro@chaordicsystems.com',
      license='GPL',
      packages=['ldap_simple_search'],
      install_requires=[
          'python-ldap',
      ],
      zip_safe=False)
