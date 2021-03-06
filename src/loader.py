from __future__ import print_function
import httplib2
import os
import os.path
import io
import tempfile
import logging
import csv
import sys
import math

import pymysql

import apiclient
from apiclient import discovery
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    # Not using dotenv, assuming that ENV vars are already setup
    pass

__author__ = "Ryan Parrish <ryan@stickystyle.net>"

SCOPES = ['https://www.googleapis.com/auth/drive.metadata',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive.readonly']
CLIENT_SECRET_FILE = os.environ.get('CLIENT_SECRET_FILE') or 'client_secrets.json'
APPLICATION_NAME = 'SheetsETL'

SQL_SOURCE = os.environ.get("SQL_SOURCE")
SHEET_DEST = os.environ.get("SHEET_DEST")

logger = logging.getLogger(__name__)
rootlogger = logging.getLogger()
rootlogger.setLevel(logging.getLevelName(str(os.environ.get('LOG_LEVEL') or 'INFO').upper()))
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
rootlogger.addHandler(ch)


g_discovery_logger = logging.getLogger('googleapiclient.discovery')
g_discovery_logger.setLevel('WARN')
g_discovery_logger.addHandler(ch)


connection = pymysql.connect(host=os.environ.get("MYSQL_HOST"),
                             port=int(os.environ.get("MYSQL_PORT")),
                             db=os.environ.get("MYSQL_DB"),
                             user=os.environ.get("MYSQL_USER"),
                             passwd=os.environ.get("MYSQL_PASSWD"))


def convert_size(size):
    """
    http://stackoverflow.com/a/18650828/959342

    :param size: Size in bytes to convert
    :return: String representation of the size
    :rtype: str
    """
    if size == 0:
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    :return: Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets-etl.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        tools.run_flow(flow, store)
        logger.info('Storing credentials to %s', credential_path)
        logger.info('Please run the script again')
        sys.exit()
    return credentials


def get_files_in_folder(folder_id):
    """Print files belonging to a folder.

    :param folder_id: ID of the folder to list files from.
    :return: Iterator for files in a google drive folder
    """
    service = discovery.build('drive', 'v3', requestBuilder=build_request)
    page_token = None
    while True:
        response = service.files().list(q="'{}' in parents and trashed=false".format(folder_id),
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name, mimeType)',
                                        pageToken=page_token).execute()
        for ff in response.get('files', []):
            yield ff
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break


def download_file(file_id):
    """Download a file from google drive.

    :param file_id: ID of the file to download.
    :return: Content of file downloaded
    """
    service = discovery.build('drive', 'v3', requestBuilder=build_request)
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    logger.debug("Begin downloading %s", file_id)
    while done is False:
        status, done = downloader.next_chunk()
        logger.debug("Download %d%%. of %s", int(status.progress() * 100), file_id)
    logger.debug("Done downloading %s", file_id)
    return fh.getvalue()


def upload_file(file_ref, file_source, file_folder):
    """Upload and convert the CSV file

    :param file_ref: Dict containing metadata about file
    :param file_source: File like object to upload
    :param file_folder: Folder to place resulting google sheets into.
    """
    service = discovery.build('drive', 'v3', requestBuilder=build_request)
    file_metadata = {'name': file_ref['name'].replace('.sql', ''),
                     'mimeType': 'application/vnd.google-apps.spreadsheet',
                     'parents': [file_folder]
                     }
    logger.info("Uploading file %s", file_metadata['name'])
    media = MediaIoBaseUpload(file_source, mimetype='text/csv', resumable=True)

    existing_id = None
    for ff in get_files_in_folder(folder_id=file_folder):
        logger.debug(ff)
        if (ff.get('mimeType') == 'application/vnd.google-apps.spreadsheet') and (ff.get('name') == file_metadata['name']):
            existing_id = ff.get('id')

    response = None
    logger.debug("Begin writing to google sheets")
    try:
        if existing_id:
            logger.debug("Found existing sheet: %s, will update it" % existing_id)
            del file_metadata['parents']  # .update() doesn't allow 'parents' prop
            request = service.files().update(fileId=existing_id,
                                             body=file_metadata,
                                             media_body=media,
                                             fields='id')
        else:
            logger.debug("Writing new sheet")
            request = service.files().create(body=file_metadata,
                                             media_body=media,
                                             fields='id')
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.debug("Uploaded %d%%." % int(status.progress() * 100))
    except apiclient.errors.HttpError as e:
        logger.error(e)
        return None

    logger.debug("Uploaded 100%")
    logger.info('Finished loading file %s', file_metadata['name'])


def get_sql_files(folder_id):
    """Download a file from google drive.

    :param folder_id: ID of the folder to search for SQL files
    """
    queries = []
    for ff in get_files_in_folder(folder_id=folder_id):
        logger.debug("Found file %s in %s", ff.get('name'), SQL_SOURCE)
        if (ff.get('mimeType') in ('text/plain', 'text/x-sql')) and ('.sql' in ff.get('name')):
            logger.info("Found valid SQL file %s", ff.get('name'))
            sql_file = download_file(file_id=ff.get('id'))
            ff['q'] = sql_file
            queries.append(ff)
    return queries


def build_request(*args, **kwargs):
    """
    Create a new Http() object for every request, needed because httplib2 is not threadsafe.
    https://developers.google.com/api-client-library/python/guide/thread_safety

    :param args:
    :param kwargs:
    :return: Http() object to use in the service builder
    :rtype: apiclient.http.HttpRequest
    """
    credentials = get_credentials()
    new_http = credentials.authorize(httplib2.Http())
    return apiclient.http.HttpRequest(new_http, *args, **kwargs)


def main():
    logger.info("Starting process")
    queries = get_sql_files(folder_id=SQL_SOURCE)

    for query in queries:
        with connection.cursor() as cursor:
            logger.info("Executing query for file %s", query['name'])
            try:
                cursor.execute(query['q'])
            except pymysql.err.ProgrammingError:
                logger.exception("SQL syntax error")
                continue
        csv_header = [x[0] for x in cursor.description]
        logger.debug("Writing CSV file for %s", query['name'])
        logger.debug('gettempdir(): %s', tempfile.gettempdir())
        temp = tempfile.TemporaryFile()
        c = csv.writer(temp)
        c.writerow(csv_header)
        total_cells = 0
        column_count = len(csv_header)
        total_cells += column_count
        for row in cursor:
            c.writerow(row)
            total_cells += column_count
        tmp_size = temp.tell()
        logger.info("Done writing intermediate CSV file for %s. File is %s, %s cells",
                    query['name'], convert_size(tmp_size), total_cells)
        if total_cells >= 2000000:
            logger.error("Resulting intermediate file is over the 2 million cell drive API limit, we'll have to skip it")
            temp.close()
            continue
        temp.seek(0)
        upload_file(file_ref=query, file_source=temp, file_folder=SHEET_DEST)
        temp.close()


if __name__ == '__main__':
    main()
