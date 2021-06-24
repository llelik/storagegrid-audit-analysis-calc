#!/usr/bin/env python3

#################################################################################
#  [SGAC(CSV)] - Python and R scripts for NetApp StorageGRID Audit Log Analysis #
#  License: The MIT License                                                     #
#  Date: 2021/06/23                                                             #
#  Authors: Vishnu Vardhan, scaleoutSean                                        #
#  URL: https://github.com/scaleoutsean/storagegrid-audit-analysis              #
#################################################################################

import re as re
import csv
import argparse
from pathlib import Path

def process_line(line,row_number,showback):

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
                if (showback == True and (key not in showback_includes)):
                    continue
                else:
                    myLine[key] = val
            else:
                debug_file.write("Missing value in source file, row:", row_number)
        else:
            debug_file.write("Did not extract key in source file, row: ", row_number)
    if ((showback == True) and (myLine['ATYP'] not in showback_items)):
        return None
    else:
        return myLine

#### Main Starts Here

parser = argparse.ArgumentParser(description='Convert NetApp StorageGRID audit log file to CSV')
parser.add_argument("source_file", help="Audit log file to convert to csv", type = str)
parser.add_argument("destination_file", help="The CSV file to generate", type = str)
parser.add_argument("debug_file", help="The debug file to log rows that cannot be parsed", type = str)
parser.add_argument("--data", help="Optional switch to only capture S3- and ILM-related events. One of: all, showback. Default: all.", type = str, default=all)

args = parser.parse_args()

row_number = 0
showback = False

fieldnames = ['Timestamp', 'AMID', 'ANID', 'ASES', 'ASQN', 'ATID', 'ATIM', 'ATYP', 'AVER', 'CBID', 'CNDR', 'CNID', 'CSIZ', 'CTAS', 'CTDR', 'CTDS', 'CTES', 'CTSR', 'CTSS', 'DAIP', 'GNDV', 'GNGP', 'GNIA', 'GNID', 'GNTP', 'HSID', 'HTRH', 'INIE', 'LOCS', 'MDIP', 'MDNA', 'MPAT', 'MPQP', 'MRBD', 'MRMD', 'MRSC', 'MRSP', 'MSIP', 'MTME', 'MUUN', 'OBCL', 'OCBD', 'OUID', 'PATH', 'RSLT', 'RUID', 'RULE', 'S3AI', 'S3AK', 'S3BK', 'S3KY', 'SACC', 'SAIP', 'SBAC', 'SBAI', 'SEGC', 'SEID', 'SGCB', 'SPAR', 'SRCF', 'STAT', 'SUSR', 'SVIP', 'TIME', 'TLIP', 'ULID', 'UUID']

if Path(args.destination_file).is_file():
    print("Error: destination file exists. We will not overwrite existing output or debug file.")
    exit(1)

if (args.data == 'showback'):
    showback = True
    showback_items = ['ORLM', 'SDEL', 'SGET', 'SHEA', 'SPUT']
    showback_includes = ['Timestamp', 'AMID', 'ATYP', 'CNID', 'CSIZ', 'PATH', 'RSLT', 'RULE', 'SACC', 'SAIP', 'SBAC', 'SBAI', 'STAT', 'SUSR', 'TIME', 'TLIP']
    print("Showback filter is ON. Extracting only the rows with ATYP events:", showback_items)
    print("The following subset of columns will be included:", showback_includes )

# if (args.data == 'mgmt'):
    #showback = True
    # showback_items = ['MDIP', 'MDNA', 'MPAT', 'MPQP', 'MRBD', 'MRMD', 'MRSC', 'MRSP', 'MSIP', 'MUUN', 'RSLT']
    # TODO showback_includes = ['Timestamp', 'AMID', 'ATYP', 'CNID', 'CSIZ', 'PATH', 'RSLT', 'RULE', 'SACC', 'SAIP', 'SBAC', 'SBAI', 'STAT', 'SUSR', 'TIME', 'TLIP']
    # print("Management Audit filter is ON. Extracting only the rows with MGAU events:", showback_items)
    # print("The following subset of columns will be included:", showback_includes )

with open(args.destination_file, 'w') as csv_file:
    if (showback == True):
        writer = csv.DictWriter(csv_file, fieldnames = showback_includes)
    else: 
        writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
    writer.writeheader()

    with open(args.debug_file, 'w') as debug_file:
        debug_file.write('Rows with problems:\n')

    with open(args.source_file, "r") as f:
        for l in f:
            row_number = row_number + 1
            myRow = process_line(l, row_number, showback)
            if myRow != None:
                writer.writerow(myRow)

print("Parsed lines in audit log file", args.source_file, "file:", row_number)
