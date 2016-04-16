**Sheets Query**

This a tool that runs a series of .sql files within a Google drive folder, and writes the results as a native google sheet into another folder.
This serves as a simple ETL tool that the spreadsheet type people can then slice the data how they like.

**Setup**

1. Checkout repo
    - `$git clone https://github.com/stickystyle/SheetsETL.git`
2. Create VirtualEnv within the checked out folder
    - `$virtualenv create venv`
3. Activate the VirtualEnv
    - `$source venv/bin/activate`
4. Install the requirements
    - `$pip install -r requirements.txt`
5. Create the .env to store your environmental variables if they don't exist in your env...
    - SQL_SOURCE is the google drive folder id where the source SQL files live
    - SHEET_DEST is the google drive folder id where the generated sheets will be written to
    - MYSQL_HOST is the location of the MySQL server you want to query
    - MYSQL_PORT is the port to connect to
    - MYSQL_USER is the user to connect to the MySQL server as. See security notice
    - MYSQL_PASSWD is the password for the above user
    - SQL_SOURCE is the folder that contains the SQL query files to run.
    - SHEET_DEST is the folder that the resulting sheets will be placed in.
    `MYSQL_HOST=db.example.com`  
    `MYSQL_PORT=3306`  
    `MYSQL_DB=my_database`  
    `MYSQL_USER=db_user`  
    `MYSQL_PASSWD=ASweetPassword`  
    `SQL_SOURCE=0B_jczERcXKwsUEt5dGtrV1h4Y1E`
    `SHEET_DEST=0B_jczERcXKwsYzVsNHFIMDktZ2c`
6. Optional, install [Drive Notepad](https://chrome.google.com/webstore/detail/drive-notepad/gpgjomejfimnbmobcocilppikhncegaj?hl=en-GB) to make editing of SQL files easier within Chrome.

**Usage**

Create a plain text file with the .sql extension in the `SQL_SOURCE`, then run the loader.py script.
The script will iterate through all .sql files in the `SQL_SOURCE` folder, execute the query contained
in the file, then create a native Google Sheet in the `SHEET_DEST` folder containing the results of the query.


**Loading data**

Simply execute the `loader.py` script with the VirtualEnv activated.  
It can also be ran easily (in cases such as CRON) within a wrapper script like so...

    #!/bin/bash
    cd /opt/SheetsETL
    source venv/bin/activate
    python loader.py

**Security Notice**

With this tool, you are enabling anyone that has access to the SQL_SOURCE folder to be
able to write queries to your server, you need to think about your data security before you distribuite
access to this tool.

My personal deployment has `MYSQL_HOST` being a read-only
replica of my main database, and the database defined in `MYSQL_DB` is a demoralized copy
of only the data that is needed by the annalists at my company. This eliminates the ability for someone
to write statements that can change data, and we ensure that users are not able to select data we don't want
them to.

The first time loader.py is ran you will be prompted to authorize the the application with your google account, the script
currently needs three permission scopes as documented [here](https://developers.google.com/drive/v2/web/scopes#google_drive_scopes).
  - `https://www.googleapis.com/auth/drive.metadata`
    - Allows read-write access to file metadata, but does not allow any access to read, download, write or upload file content. Does not support file creation, trashing or deletion. Also does not allow changing folders or sharing in order to prevent access escalation.
  - `https://www.googleapis.com/auth/drive.file`
    - Per-file access to files created or opened by the app
  - `https://www.googleapis.com/auth/drive.readonly`
    - Allows read-only access to file metadata and file content