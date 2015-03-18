GData-Backup
============

A simple script to back up data from Google Services. Currently supports backing up contacts only.

To Do
-----

 * Implement calendar backup
 * Implement restore functions

Dependencies
------------

 * Protocol Buffers (https://developers.google.com/protocol-buffers/)

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