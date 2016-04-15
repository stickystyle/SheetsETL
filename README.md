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
    - SQL_SOURCE and SHEET_DEST are the google drive folder id's.
        - SQL_SOURCE is the folder that contains the SQL query files to run.  
        - SHEET_DEST is the folder that the resulting sheets will be placed in.  
    `MYSQL_HOST=db.example.com`  
    `MYSQL_PORT=3306`  
    `MYSQL_DB=my_database`  
    `MYSQL_USER=db_user`  
    `MYSQL_PASSWD=ASweetPassword`  
    `SQL_SOURCE=0B2ZcBQIgauDfczJJb2REU0xWSGc`  
    `SHEET_DEST=0B2ZcBQIgauDfTkJ5ektXbU5raGs`
6. Optional, install [Drive Notepad](https://chrome.google.com/webstore/detail/drive-notepad/gpgjomejfimnbmobcocilppikhncegaj?hl=en-GB) to make editing of SQL files easier within Chrome.

**Running**

Simply execute the `loader.py` script with the VirtualEnv activated.  
It can also be ran (in cases such as CRON) within a wrapper script like so...  

    #!/bin/bash
    cd /opt/SheetsETL
    source venv/bin/activate
    python loader.py
