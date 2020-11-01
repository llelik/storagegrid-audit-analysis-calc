#!/usr/bin/env python3

#################################################################################
#  [SGAC(CSV)] - Python and R scripts for NetApp StorageGRID Audit Log Analysis #
#  License: The MIT License                                                     #
#  Date: 2020/11/01                                                             #
#  Authors: Vishnu Vardhan, scaleoutSean                                        #
#  URL: https://github.com/scaleoutsean/storagegrid-audit-analysis              #
#################################################################################

import re as re
import csv
import argparse
from pathlib import Path

def process_one_audit_log_line(line,row_number):

    myLine = dict()
    new_line = re.sub(r'\([a-zA-Z0-9_]*\)', '', line)
    s = re.split(" ", new_line, 1)
    time = s[0]
    remaining = s[1]
    myLine['Timestamp'] = time
    m = re.match(r'\[AUDT\:(.*)\]', remaining)
    audit_msg = m.group(1)
    n = re.findall(r'(\[([A-Z]{4}:.*?)\](?=\[))', audit_msg)
    for i in n:
        keyval = i[1]
        o = re.match(r'([A-Z]{4}):(.*)', keyval)
        if ((o.group(1) != None)):
            key = o.group(1)
            val = o.group(2)
            if (val != None):
                myLine[key] = val
            else:
                debug_file.write(row_number)
        else:
            debug_file.write(row_number, ",", keyval)
    return myLine

#### Main Starts Here

parser = argparse.ArgumentParser(description='Convert NetApp StorageGRID audit log file to CSV')
parser.add_argument("source_file", help="Audit log file to convert to csv", type = str)
parser.add_argument("destination_file", help="The CSV file to generate", type = str)
parser.add_argument("debug_file", help="The debug file to log rows that cannot be parsed", type = str)

args = parser.parse_args()

row_number = 0

fieldnames = ['Timestamp', 'AMID', 'ANID', 'ASES', 'ASQN', 'ATID', 'ATIM', 'ATYP', 'AVER', 'CBID', 'CNDR', 'CNID', 'CSIZ', 'CTAS', 'CTDR', 'CTDS', 'CTES', 'CTSR', 'CTSS', 'DAIP', 'GNDV', 'GNGP', 'GNIA', 'GNID', 'GNTP', 'HSID', 'HTRH', 'INIE', 'LOCS', 'MDIP', 'MDNA', 'MPAT', 'MPQP', 'MRBD', 'MRMD', 'MRSC', 'MRSP', 'MSIP', 'MUUN', 'OBCL', 'OCBD', 'OUID', 'PATH', 'RSLT', 'RUID', 'RULE', 'S3AI', 'S3AK', 'S3BK', 'S3KY', 'SACC', 'SAIP', 'SBAC', 'SBAI', 'SEGC', 'SEID', 'SGCB', 'SPAR', 'SRCF', 'STAT', 'SUSR', 'SVIP', 'TIME', 'TLIP', 'ULID', 'UUID']

if Path(args.destination_file).is_file():
    print("Error: destination file exists. We will not overwrite");
    exit(1)

with open(args.destination_file, 'w') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
    writer.writeheader()

    with open(args.debug_file, 'w') as debug_file:
        debug_file.write('Rows with problems:\n')

    with open(args.source_file, "r") as f:
        for l in f:
            myRow = process_one_audit_log_line(l, row_number)
            row_number = row_number + 1
            writer.writerow(myRow)

print("Rows processed:", row_number)
