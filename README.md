**SheetsETL**

This a tool that runs a series of .sql files within a Google drive folder, and writes the results as a native google sheet into another folder.
This serves as a simple ETL tool that the spreadsheet type people can then slice the data how they like.
A lot of the code is actually copy/paste from from various Google API examples, we're just piecing it together.

**Setup**

1. Setup your OAUTH 2.0 [server-side flow](https://developers.google.com/drive/v2/web/auth/web-server) in the Google devleopers console.
When you've finished the setup at Google, place the `client_secrets.json` file you downloaded in the directory with
 `loader.py`
2. Install the requirements (preferably in a virtualenv)
    - `$pip install -r requirements.txt`
3. Create the .env to store your environmental variables if they don't exist in your environment already...
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
6. Optional, install [Drive Notepad](https://chrome.google.com/webstore/detail/drive-notepad/gpgjomejfimnbmobcocilppikhncegaj) to make editing of SQL files easier directly in the google drive web interface.

**Usage**

Create a plain text file with the .sql extension in the `SQL_SOURCE`, then run the loader.py script.
The script will iterate through all .sql files in the `SQL_SOURCE` folder, execute the query contained
in the file, then create a native Google Sheet in the `SHEET_DEST` folder containing the results of the query.

It can also be ran easily (in cases such as CRON) within a wrapper script like so...

    #!/bin/bash
    cd /opt/SheetsETL
    source venv/bin/activate
    python loader.py

Additionally there is a Docker image [stickystyle/sheetsetl](https://hub.docker.com/r/stickystyle/sheetsetl/) that
 can be used. Simply pull the image and start a container with the appropriate env vars set.

    $docker run -it --rm --name SheetsETL \
      MYSQL_HOST=db.example.com \
      MYSQL_PORT=3306 \
      MYSQL_DB=my_database \
      MYSQL_USER=db_user \
      MYSQL_PASSWD=ASweetPassword \
      SQL_SOURCE=0B_jczERcXKwsUEt5dGtrV1h4Y1E \
      SHEET_DEST=0B_jczERcXKwsYzVsNHFIMDktZ2c \
      stickystyle/sheetsetl

**Limitations**

[Google sheets has a limitation](https://support.google.com/drive/answer/37603?hl=en) of two million cells per spreadsheet, this includes all of the sheets ('tabs')
that exist in the spreadsheet. So be mindful of the amount of rows and columns your query returns.

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