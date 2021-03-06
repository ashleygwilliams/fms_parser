#!/usr/bin/env python2

import datetime
import download_fms_fixies
import os
import pandas as pd
import pandas.io.sql
import parse_fms_fixies_2
import sqlite3
import sys

# script must be run from fms_parser/code directory
if not os.path.split(os.getcwd())[-1] == 'code':
	if os.path.split(os.getcwd())[-1] == 'fms_parser':
		os.chdir('code')
		print '\n*INFO: current working directory set to', os.getcwd()
	else:
		raise Exception('This script must be run from the fms_parser/code directory!')

# auto-make data directories, if not present
FIXIE_DIR = os.path.join('..', 'data', 'fixie')
DAILY_CSV_DIR = os.path.join('..', 'data', 'daily_csv')
LIFETIME_CSV_DIR = os.path.join('..', 'data', 'lifetime_csv')
os.system('mkdir -pv ' + FIXIE_DIR)
os.system('mkdir -pv ' + DAILY_CSV_DIR)
os.system('mkdir -pv ' + LIFETIME_CSV_DIR)

## DOWNLOAD! ##################################################################
# test for existence of downloaded fixies
test_fixies = sorted([f for f in os.listdir(FIXIE_DIR) if f.endswith('.txt')])
# if none, start from THE BEGINNING
if len(test_fixies) == 0:
	start_date = datetime.date(2005, 6, 9)
# else start from last available fixie date
else:
	start_date = parse_fms_fixies_2.get_date_and_day(test_fixies[-1])[0]
# always end with today
end_date = datetime.date.today()

# download all teh fixies!
fnames = download_fms_fixies.download_fixies(start_date, end_date)

# check all downloaded fixies against all parsed csvs
downloaded_files = set([fixie.split('.')[0] for fixie in os.listdir(FIXIE_DIR)
	if fixie.endswith('.txt')])
def parsed_files():
	return set([csv.split('_')[0] for csv in os.listdir(DAILY_CSV_DIR) if csv.endswith('.csv')])

## PARSE! #####################################################################
# fixies that have not yet been parsed into csvs
new_files = sorted(list(downloaded_files.difference(parsed_files())))
# parse all teh fixies!
for f in new_files:
	fname = os.path.join(FIXIE_DIR, f+'.txt')
	#print '\n', fname
	dfs = parse_fms_fixies_2.parse_file(fname, verbose=False)

	# each table for each date stored in separate csv files
	for i, df in dfs.items():
		daily_csv = os.path.join(DAILY_CSV_DIR, f.split('.')[0]+'_t'+str(i)+'.csv')
		df.to_csv(daily_csv,
			index=False, header=True, encoding='utf-8', na_rep='')

# iterate over all fms tables
for i in range(1,9):

	# create the lifetime csv files it they don't exist
	lifetime_csv = os.path.join(LIFETIME_CSV_DIR, 'table_'+str(i)+'.csv')

	# if it doesn't exist
	if not os.path.isfile(lifetime_csv):
		lifetime = open(lifetime_csv, 'ab')
		# add the header
		lifetime.write(open(os.path.join(DAILY_CSV_DIR, list(parsed_files())[0]+'_t'+str(i)+'.csv')).readline())
		lifetime.close()

	# append new csvs to lifetime csvs
	for f in new_files:

		# we have no idea why it's giving us a blank file
		if len(f) == 0: continue

		daily_csv = os.path.join(DAILY_CSV_DIR, f.split('.')[0]+'_t'+str(i)+'.csv')

		lifetime = open(lifetime_csv, 'ab')
		daily = open(daily_csv, 'rb')

		daily.readline() # burn header
		for line in daily:
			lifetime.write(line)
		daily.close()


csv_txt = r"""
      ,----..    .--.--.
     /   /   \  /  /    '.       ,---.
    |   :     :|  :  /`. /      /__./|
    .   |  ;. /;  |  |--`  ,---.;  ; |
    .   ; /--` |  :  ;_   /___/ \  | |
    ;   | ;     \  \    `.\   ;  \ ' |
    |   : |      `----.   \\   \  \: |
    .   | '___   __ \  \  | ;   \  ' .
    '   ; : .'| /  /`--'  /  \   \   '
    '   | '/  :'--'.     /    \   `  ;
    |   :    /   `--'---'      :   \ |
     \   \ .'                   '---"
      `---`
"""
soundsystem_txt = r"""
.-. .-. . . . . .-. .-. . . .-. .-. .-. .  .
`-. | | | | |\| |  )`-.  |  `-.  |  |-  |\/|
`-' `-' `-' ' ` `-' `-'  `  `-'  '  `-' '  `
"""
print csv_txt
print soundsystem_txt
print '*http://csvsoundsystem.com/'

TABLES = [
    {
        'raw-table': 1,
        'new-table': 't1',
    },
    {
        'raw-table': 2,
        'new-table': 't2a',
    },
    {
        'raw-table': 3,
        'new-table': 't2b',
    },
    {
        'raw-table': 4,
        'new-table': 't3a',
    },
    {
        'raw-table': 5,
        'new-table': 't3b',
    },
    {
        'raw-table': 6,
        'new-table': 't3c',
    },
    {
        'raw-table': 7,
        'new-table': 't4_t5',
    },
    {
        'raw-table': 8,
        'new-table': 't6',
    },
]

connection = sqlite3.connect(os.path.join('..', 'data', 'fms.db'))
connection.text_factory = str # bad, but pandas doesn't work otherwise

for table in TABLES:
    df = pandas.read_csv(os.path.join('..', 'data', 'lifetime_csv', 'table_%d.csv' % table['raw-table']))
    pandas.io.sql.write_frame(df, '_t%d' % table['raw-table'], connection)
    connection.execute('DROP TABLE IF EXISTS "%s";' % table['new-table'])
    connection.execute('ALTER TABLE "_t%d" RENAME TO "%s";' % (table['raw-table'], table['new-table']))

# Table 4 and table 5 views
connection.execute('''
CREATE VIEW IF NOT EXISTS t4 AS
SELECT * FROM t4_t5 WHERE "table" LIKE "TABLE IV%";
''')
connection.execute('''
CREATE VIEW IF NOT EXISTS t5 AS
SELECT * FROM t4_t5 WHERE "table" LIKE "TABLE V%";
''')

# Commit
connection.commit()


# Brian's tests go here. Look at is_it_running.py if you want to make the date stuff fancier.
t1 = pandas.io.sql.read_frame('''SELECT * FROM "t1" WHERE date = '%s';''' % datetime.date.today().isoformat(), connection)
