#!/usr/bin/env python3

#################################################################################
#  [SGAC] - NetApp StorageGRID Audit-log Converter to JSON                      #
#  License: The MIT License                                                     #
#  Date: 2021/10/20 (v0.2.2)                                                    #
#  Authors: scaleoutSean                                                        #
#  URL: https://github.com/scaleoutsean/storagegrid-audit-analysis              #
#################################################################################

from builtins import Exception, ValueError, all, enumerate, exit, int, isinstance, open, print, str
from pathlib import Path
import argparse
import json
import regex as re


def process_line(line,row_number):
    new_line = re.sub(r'\([a-zA-Z0-9_]*\)', '', line)
    s = re.split(" ", new_line, 1)
    m = re.match(r'\[AUDT\:(.*)\]', s[1])
    audit_msg = m.group(1)
    n = re.findall(r'\[[A-Z]{1}[A-Z0-9]{1}[A-Z]{2}:.*?\](?=\[|$)', audit_msg)
    edict = {}
    edict['Timestamp'] = s[0]
    for i in n:
        i = re.sub(r'(^\[)|(\]$)', '', i)
        i = re.sub(r'(?<=[A-Z]{1}[A-Z0-9]{1}[A-Z]{2}):', '\t', i)
        s = re.split('\t', i, 1)
        e1 = s[0]
        e2 = re.sub(r'(^")|("$)', '', s[1])
        if e1 == "SRCF" or e1 == "MRBD" or e1 == "MRSP" or e1 == "SRCF":
            e2 = re.sub(r'\\n', r'', e2)
            e2 = re.sub(r'\\x09', r'', e2)
            e2 = re.sub(r'\\', r'', e2)
        edict[e1] = e2
    json_data = json.dumps(edict)
    if validate_json(json_data) == True:
        sgac_json = json.loads(json_data, object_hook=_decode)
    else:
        print("Bad JSON from log line", row_number)
    return sgac_json


def validate_json(json_data):
    try:
        json.loads(json_data)
        return True
    except json.decoder.JSONDecodeError as err:
        print("Invalid JSON") # in case json is invalid
        print(err)
        return False


def _decode(o):
    # https://stackoverflow.com/a/48401729/3284957
    if isinstance(o, str):
        try:
            return int(o)
        except ValueError:
            return o
    elif isinstance(o, dict):
        return {k: _decode(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [_decode(v) for v in o]
    else:
        return o


def fix_line(line):
    if 'ATID' in line:
        if type(line['ATID']) == int:
            line['ATID'] = str(line['ATID'])
    if 'S3AI' in line:
        if type(line['S3AI']) == int:
            line['S3AI'] = str(line['S3AI'])
    if 'SBAI' in line:
        if type(line['SBAI']) == int:
            line['SBAI'] = str(line['SBAI'])
    return line


parser = argparse.ArgumentParser(description="Convert NetApp StorageGRID audit log file to JSON")
parser.add_argument("--source_file", "-s", "-src", "--source", required=True, help="Source (audit log) file", type = str)
parser.add_argument("--destination_file", "-d", "-dst", "--destination", required=True, help="Destination file (JSON)", type = str)
parser.add_argument("--max_fsize", required=True, help="Bottom file size limit", type = int)
parser.add_argument("--report_file", "-r", help="Calculation report destination file", type = str)
args = parser.parse_args()

row_number = 0
stats_dict = {}
print(args.max_fsize)
with open(args.destination_file, 'w') as json_file:
    with open(args.source_file, "r") as f:
        for l in f:
            row_number    = row_number + 1
            sgac_json     = process_line(l, row_number)
            sgac_json_fix = fix_line(sgac_json)
            # my code begin
            
            try:
                if sgac_json['ATYP'] == 'SPUT' and sgac_json['CSIZ'] < args.max_fsize:
                   try:
                      Cnt_curr = stats_dict[sgac_json['SBAC']]['Cnt']
                      Size_curr = stats_dict[sgac_json['SBAC']]['Size']
                      stats_dict[sgac_json['SBAC']] = {'Cnt': Cnt_curr + 1, 'Size': Size_curr + sgac_json['CSIZ']} 
                   except:
                      print('Adding new Acc: ', sgac_json['SBAC'])
                      stats_dict[sgac_json['SBAC']] = { 'Cnt': 0, 'Size': 0}
                      Cnt_curr = stats_dict[sgac_json['SBAC']]['Cnt']
                      Size_curr = stats_dict[sgac_json['SBAC']]['Size']
                      stats_dict[sgac_json['SBAC']] = {'Cnt': Cnt_curr + 1, 'Size': Size_curr + sgac_json['CSIZ']}

            except:
                print('Excluded oper type: ', sgac_json['ATYP'])
            if sgac_json['ATYP'] == 'OVWR':
                print('Overwrite = ', sgac_json['PATH'] )
            # my code end    
            json.dump(sgac_json_fix, json_file)
            json_file.write('\n')
        print("Number of lines parsed from file", args.source_file, ":", row_number)

with open(args.report_file, 'w') as rep_file:
    json.dump(stats_dict, rep_file)
    rep_file.write('\n')


print('Statistics: ', '\n')
print(stats_dict)