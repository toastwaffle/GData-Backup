GData-Backup
============

A simple script to back up data from Google Services. Currently supports backing up contacts and calendar.

To Do
-----

 * Implement restore functions

Dependencies
------------

 * Protocol Buffers with Python Bindings (https://developers.google.com/protocol-buffers/)
 * GFlags for Python (http://code.google.com/p/python-gflags)
 * Google Data APIs Python Client Library (https://code.google.com/p/gdata-python-client/)
 * Google Discovery API Python Client Library (https://github.com/google/google-api-python-client)

Instructions
------------

 1. Compile protocol buffer definitions
 ```
 protoc --python_out=. *.proto
 ```

 2. Make a storage directory
 ```
 mkdir ~/gdata
 ```

 3. Run
 ```
 ./backup.py --storage_dir=~/gdata --contacts
 ```
