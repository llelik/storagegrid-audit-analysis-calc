# StorageGRID Audit Analysis

## Table of Content

- [StorageGRID Audit Analysis](#storagegrid-audit-analysis)
  - [Table of Content](#table-of-content)
  - [About StorageGRID Audit Log](#about-storagegrid-audit-log)
    - [Tools](#tools)
      - [Sample audit-explain output](#sample-audit-explain-output)
      - [Sample audit-sum output](#sample-audit-sum-output)
    - [StorageGRID Sample Log Entry (ATYP = S3 PUT)](#storagegrid-sample-log-entry-atyp--s3-put)
    - [Q&A about StorageGRID Audit Files](#qa-about-storagegrid-audit-files)
      - [How to read audit messages](#how-to-read-audit-messages)
      - [What if I'm just interested in S3 PUT/GET/DELETE to figure out who's using how much](#what-if-im-just-interested-in-s3-putgetdelete-to-figure-out-whos-using-how-much)
      - [What else related to consumption and utilization can I find in StorageGRID audit log](#what-else-related-to-consumption-and-utilization-can-i-find-in-storagegrid-audit-log)
      - [What is tricky about analyzing ILM, and bucket or group access policies](#what-is-tricky-about-analyzing-ilm-and-bucket-or-group-access-policies)
      - [Is there a list of all fields/keys for StorageGRID logs](#is-there-a-list-of-all-fieldskeys-for-storagegrid-logs)
      - [How can one ensure that no audit log file is deleted before it's copied out of Admin Node](#how-can-one-ensure-that-no-audit-log-file-is-deleted-before-its-copied-out-of-admin-node)
  - [Scripts and utilities in this repository](#scripts-and-utilities-in-this-repository)
    - [[SGAC(CSV)] - StorageGRID Audit Log CSV Converter](#sgaccsv---storagegrid-audit-log-csv-converter)
      - [How to run](#how-to-run)
        - [Complete Audit Log File (Full Mode)](#complete-audit-log-file-full-mode)
        - [Partial Audit Log File (Showback Mode)](#partial-audit-log-file-showback-mode)
      - [Sample [SGAC(CSV]) Output](#sample-sgaccsv-output)
      - [Next Steps with [SGAC(CSV)] output](#next-steps-with-sgaccsv-output)
      - [Known issues and limitations](#known-issues-and-limitations)
      - [Performance](#performance)
      - [Change Log](#change-log)

## About StorageGRID Audit Log

Links in this section lead to the official NetApp StorageGRID documentation (v11.4 at the moment) to avoid repeating what's already in the manual.

### Tools

Audit-sum and audit-explain live in Admin Node(s). They're not meant to turn Admin Nodes into analytics clusters, so consider doing analytics externally or maybe running these on Backup Admin Node

- [audit-sum](http://docs.netapp.com/sgws-114/topic/com.netapp.doc.sg-audit/GUID-F1733A2C-E1D8-4798-9805-682E75F43629.html): tool available in Admin Nodes (in the container), has 3-4 switches to summarize types of traffic from compressed or non-compressed ("live") logs
- [audit-explain](http://docs.netapp.com/sgws-114/topic/com.netapp.doc.sg-audit/GUID-09E4272A-49E7-4E6C-B9F5-F977B4EE2E5A.html): tool also available in Admin Nodes (in the container), can extract lines from StorageGRID logs and output in the common space-delimited format that can be handled by regular programmers or maybe even Excel. Note that audit-explain cannot work on compressed log files. It may be sufficient for usage analysis of lightly used grids
- [SGAC(CSV)] - Storage Grid Audit Log Converter (to CSV) - see further below

#### Sample audit-explain output

```raw
SPUT S3 PUT object cbid:CA681D278A779FEE uuid:2EC5D4B4-7266-4E16-8FDD-0881A496CEF2 tenant:93303750965081886661 client:10.249.56.126 load_balancer:10.128.59.214 bytes:32000 usec:23904  path:two-b2/testobject-995
SHEA S3 HEAD object cbid:CA681D278A779FEE uuid:2EC5D4B4-7266-4E16-8FDD-0881A496CEF2 tenant:93303750965081886661 client:10.249.56.126 load_balancer:10.128.59.214 bytes:32000 usec:4155  path:two-b2/testobject-995
SDEL S3 DELETE object cbid:F23E9AA897531DC5 uuid:BB30ECE2-F5E9-4064-AD31-15A526BD7E75 tenant:93303750965081886661 client:10.249.56.126 load_balancer:10.128.59.214 bytes:32000 usec:10672  path:two001/testobject-995
SGET S3 GET bucket tenant:93303750965081886661 client:10.249.56.126 load_balancer:10.128.59.214 usec:26649  path:two001
ORLM Object Rules Met cbid:F23E9AA897531DC5 uuid:BB30ECE2-F5E9-4064-AD31-15A526BD7E75 purged (path two001/testobject-995)
```

#### Sample audit-sum output

This is part of a result with audit-sum executed with `-go -l`:

```raw
===== SDEL.object
  Total:             234 operations
  Slowest:         0.265 sec
  Average:         0.028 sec
  Fastest:         0.006 sec
  Slowest operations:
      time(usec)       source ip         type      size(B) path
      ========== =============== ============ ============ ====
          264727    10.249.56.34       object        32000 two-b1/testobject-245
          261394    10.249.56.34       object        32000 two-b1/testobject-112
          241311    10.249.56.34       object        10699 two-b2/027-disk-time.png
          231441    10.249.56.34       object        32000 two-b1/testobject-10
          228197    10.249.56.34       object        32000 two-b1/testobject-107
          200056    10.249.56.34       object        22507 two-b2/H615C-server-specs.png
          198887    10.249.56.34       object        32000 two-b1/testobject-237
          189713    10.249.56.34       object        64059 two-b2/Screenshot at 2020-04-14 10-40-05.png
          173622    10.249.56.34       object        32000 two-b1/testobject-114
          170490    10.249.56.34       object        32000 two-b1/testobject-239
===== SGET.bucket
  Total:              57 operations
  Slowest:         0.075 sec
  Average:         0.011 sec
  Fastest:         0.002 sec
  Slowest operations:
      time(usec)       source ip         type      size(B) path
      ========== =============== ============ ============ ====
           75025    10.249.56.34       bucket              two002/
           56259    10.249.56.34       bucket              two001/
           30216    10.249.56.34       bucket              two-b1/
           29891    10.249.56.34       bucket              sean1-b1/
           29234    10.249.56.34       bucket              two001/
           26083    10.249.56.34       bucket              sean2-b2/
           25723    10.249.56.34       bucket              two-b1/
           23964    10.249.56.34       bucket              sean2-b2/
           23066    10.249.56.34       bucket              sean1-b1/
           19580    10.249.56.34       bucket              sean1-b1/
...
```

### StorageGRID Sample Log Entry (ATYP = S3 PUT)

Line breaks were inserted for easier viewing:

```raw
2020-10-30T17:29:51.084346 [AUDT:
[RSLT(FC32):SUCS]
[CNID(UI64):1604078982714250]
[TIME(UI64):346407]
[SAIP(IPAD):"10.128.59.235"]
[TLIP(IPAD):"10.128.59.214"]
[S3AI(CSTR):"89182157694196817210"]
[SACC(CSTR):"sean_three"]
[S3AK(CSTR):"SGKHpuvjCd-ysEBx0MA0QYt6KeifUL3yPiHtp2R5xg=="]
[SUSR(CSTR):"urn:sgws:identity::89182157694196817210:user/seantwo-user2"]
[SBAI(CSTR):"89182157694196817210"]
[SBAC(CSTR):"sean_three"]
[S3BK(CSTR):"three003"]
[S3KY(CSTR):"testobject-7"]
[ULID(CSTR):"IXYD2VycKmrwS89IfRuAtNsB6JLxw7Z2wfjdT_bRT_qn-Ew2ppDeFbCPUA"]
[CBID(UI64):0x4090675BCE7E4050]
[UUID(CSTR):"FC2C5E4C-081A-42D0-8FAE-4C887B28894E"]
[CSIZ(UI64):320000000]
[AVER(UI32):10]
[ATIM(UI64):1604078991084346]
[ATYP(FC32):SPUT]
[ANID(UI32):12828498]
[AMID(FC32):S3RQ]
[ATID(UI64):7009770064519048249]
]
```

What's in it? With parameter type indicators removed:

- `TIMESTAMP` - ISO 8601 time
- `[RSLT:SUCS]` - Result. And it didn't suck - in fact it was a success!
- `[SAIP:"10.128.59.235"]` - Source IP Address (S3 Client); `HTRH`, if audit logs it, automatically includes `X-Forwarded-For` if present on the load balancer
- `[TLIP:"10.128.59.214"]` - Trusted Loadbalancer IP (Grid Network IP of StorageGrid GW VM, in this particular grid)
- `[S3AI:"89182157694196817210"]` - S3 (Tenant) Account ID (89182157694196817210)
- `[SACC:"sean_three"]` - S3 (Tenant) Account Name; empty for anonymous requestors
- `[SUSR:"urn:sgws:identity::89182157694196817210:user/seantwo-user2"]` - S3 Identity (Tenant ID 89182157694196817210 plus Full Name); empty for anonymous requests
- `[SBAC:"sean_three"]` - S3 Account Name
- `[S3BK:"three003"]` - S3 Bucket
- `[S3KY:"testobject-7"]` - S3 Key
- `[ATYP:SPUT]` - S3 PUT audit event type
- `[CSIZ:320000000]` - Content Size (bytes)

Links in here are links to the official StorageGRID documentation pages (v11.4 at the moment, although the format of audit log isn't expected to change) to avoid repeating that info.

### Q&A about StorageGRID Audit Files

#### How to read audit messages

[Start with TFM](https://docs.netapp.com/sgws-115/index.jsp?topic=%2Fcom.netapp.doc.sg-audit%2FGUID-1FD2FE07-A18F-44FA-A3B3-C7860E739A72.html&resultof=%22SUCS%22%20%22suc%22%20%22AUDT%22%20%22audt%22%20) for your version (the link is for 11.5)

#### What if I'm just interested in S3 PUT/GET/DELETE to figure out who's using how much

Check out audit-explain - it may be able to solve your problem (but pay attention to not overload Primary Admin Node).

Some keys/fields of interest:

- SPUT - S3 PUT (bytes)
- SGET - S3 GET (bytes)
- SDEL - S3 DELETE
- SHEA - S3 HEAD
- SUPD - S3 Update (e.g. Metadata)
- CSIZ - Content Size (example for StorageGRID [S3 GET](http://docs.netapp.com/sgws-114/topic/com.netapp.doc.sg-audit/GUID-223B2822-4053-4913-8B54-5D01E4186CC6.html?resultof=%22%43%53%49%5a%22%20%22%63%73%69%7a%22%20))

If Cloud Tiering is enabled and used you'd have the following SGET-equivalent traffic:

- ASCT - Archive Store (Cloud Tier) - basically egress from StorageGRID (similar to SGET in terms of network cost)
- ARCT - Archive Retrieve (Cloud Tier) - basically ingress (similar to SPUT in terms of network cost)
- SPOS - S3 POST is used to restore object from AWS Glacier storage to a Cloud Storage Pool

There are also Swift entries but barely anyone uses it so click on the audit-sum link above to see about Swift.

#### What else related to consumption and utilization can I find in StorageGRID audit log

ORLM is the ILM stuff. If you want to find those, look for audit type `ATYP` string ORLM.

In the example below we can see `RULE` that was applied was "Make 2 Copies", the default rule in StorageGRID. `PATH` tells us the ILM'd object was `testobject-7` in the bucket `three003`. Log entries are one per line (this sample has been formatted for easier viewing.)

```raw
2020-10-30T17:29:51.082431 [AUDT:
[CBID(UI64):0x4090675BCE7E4050]
[RULE(CSTR):"Make 2 Copies"]
[STAT(FC32):DONE]
[CSIZ(UI64):3383]
[UUID(CSTR):"FC2C5E4C-081A-42D0-8FAE-4C887B28894E"]
[PATH(CSTR):"three003/testobject-7"]
[LOCS(CSTR):"CLDI 12828498, CLDI 12809207"]
[RSLT(FC32):SUCS]
[AVER(UI32):10]
[ATIM(UI64):1604078991082431]
[ATYP(FC32):ORLM]
[ANID(UI32):12828498]
[AMID(FC32):OBDI]
[ATID(UI64):6800799203294572826]
]
```

Because ILM rules may apply different number of copies (or indeed, Erasure Coding) to an object, within a tenant ORLM messages may help you to figure out which application or bucket or object (name) pattern uses relatively more space or more "luxurious" ILM rules.

StorageGRID also has advanced auditing (Configuration > Audit) and protocol headers can be captured if need be (`HTRH` in audit log.)

#### What is tricky about analyzing ILM, and bucket or group access policies

Those are tricky in the sense that JSON is weirdly encoded, so it's not trivial to put it back together and present as JSON. Check the documentation on those and give it a try. Here are some examples and tips:

- [SBAC(CSTR):"solidfire"][S3BK(CSTR):"local"][S3SR(CSTR):"policy"][SRCF(CSTR):"messy JSON"]: the value of SRCF has the new ILM rule for the account "solidfire" and bucket "local"
- [MUUN(CSTR):"urn:sgws:identity::19663253853227287812:root"][MRSC(UI32):201][RSLT(FC32):SUCS][MRSP(CSTR):"messy JSON"]: the root user uploaded a new bucket policy, got the response 201 (result: success), and the response was the JSON string in MRSP
- [MRMD(CSTR):"POST"][MPAT(CSTR):"/api/v3/grid/ilm-policies"][MRSP(CSTR):"messy JSON"] - ILM policy posted
- [MRMD(CSTR):"POST"][MPAT(CSTR):"/api/v3/grid/ilm-rules"][MRSP(CSTR):"messy JSON"] - ILM rule applied
- [MRMD(CSTR):"POST"][MPAT(CSTR):"/api/v3/grid/ilm-evaluate"][MRSP(CSTR):"messy JSON"] - ILM rule evaluated
- [MRMD(CSTR):"POST"][MPAT(CSTR):"/api/v3/grid/ilm-rules/filters-validation"] - ILM filter validated; no JSON in this message
- IDEL - ILM-initiated deletion of an object
- ORLM - logged when an object is copied and stored (not deleted) thanks to ILM rules
- MGAU - management audit message (requests to the StorageGRID Management API) for every request that's not a GET or HEAD.

Management audit messages are numerous. This page in the [StorageGRID online manual](https://docs.netapp.com/sgws-115/topic/com.netapp.doc.sg-audit/GUID-21B7D957-959B-49EB-91A6-929985DBF581.html) contains a list of all management actions and codes.

To get examples of JSON output you may see encoded, refer to [Bucket and group access policies](https://docs.netapp.com/sgws-115/topic/com.netapp.doc.sg-s3/GUID-53596498-9334-44DB-A4CE-DFEC28CF21FF.html).

#### Is there a list of all fields/keys for StorageGRID logs

A lot of them (maybe not all?) are mentioned in the official documentation. I'm not aware of any omissions.

All keys found testing with a sample log from v11.5 are in the Python script. If your log contains any field that's not accounted for, you'll see them called out in console output.

#### How can one ensure that no audit log file is deleted before it's copied out of Admin Node

- Admin Node requires [200 GB space for audit logs](http://docs.netapp.com/sgws-114/topic/com.netapp.doc.sg-install-vmw/GUID-D1F77A07-11E1-4FB7-B958-B330A1C9E035.html?resultof=%22%61%75%64%69%74%2e%6c%6f%67%22%20)
- Every day logs are [rotated and compressed](http://docs.netapp.com/sgws-114/topic/com.netapp.doc.sg-audit/GUID-33B77138-D408-4D4F-9994-D2E8C3101FF2.html?resultof=%22%61%75%64%69%74%2e%6c%6f%67%22%20%22%72%6f%74%61%74%65%22%20%22%72%6f%74%61%74%22%20), so assuming 20 GB of log files per day, there's at least 24 hours to get the compressed log file out before it's deleted. The NetApp Support site has a KB about expanding the space for logs.
- You could use NetApp XCP to copy files to another share or CloudSync to copy them from NFS/SMB to S3

## Scripts and utilities in this repository

So far there's only one, `[SGAC(CSV)]`.

### [SGAC(CSV)] - StorageGRID Audit Log CSV Converter

Generates a performance report (PDF, using R) from a StorageGRID Audit Log file converted into the CSV format (Python).

Find it in the sgac directory of this repository. A subdirectory called data has a sample audit log with which the scripts used to work prior to Nov 2020 update.

![SGAC-Run-Animation](sgac/images/sgac_animated_demo.gif)

#### How to run

1. Get into the Admin Nodes (each one, if you want to not lose logs, so you want to be able to fetch them from either server) and enable NFS or SMB read-only shares of audit logs (see the StorageGRID documentation, such as [Configuring the audit client for NFS](http://docs.netapp.com/sgws-114/index.jsp?topic=%2Fcom.netapp.doc.sg-admin%2FGUID-B9B9FB7B-76FA-4C85-99A7-4310E3F24F1C.html))
2. Fetch StorageGRID log file from Admin Node (container) (NFSv3: `sg-adm1:/var/local/audit/export`; SMB: `\\sg-adm1\...`)
3. Fetch the log(s) (decompress if you've downloaded .tar.gz; you should always download compressed audit log files because they don't change)
4. Run the Python script to convert the uncompressed log file(s) to a CSV file(s)
5. Optionally, run the R script to generate a PDF report (if you don't need this report and want to use the CSV file(s) for something else)

Syntax:

`sg_audit_csv_converter.py srcFile dstFile debugFile`

`--data all` is the default (assumed) and can be omitted.

##### Complete Audit Log File (Full Mode)

- The output of this script can be used with the R script
- Only this option is meant to be used with the Python script. Output and debug file must be new (not existing) files.

```shell
python3 ./sg_audit_csv_converter.py audit.log out-file.csv debug.txt
```

##### Partial Audit Log File (Showback Mode)

- Does not have the data required for the R script
- If you want one of the following, this mode is for you:
  - Cut down on the file size and processing requirements (resources, time, disk space)
  - Somewhat (but not completely) limit the amount of possibly private or confidential data included in these reports (feel free to hack away)
  - Want to create simple show-back or charge-back reports
- Add `--data showback` to only include `ATYP` events `ORLM`, `SDEL`, `SGET`, `SHEA`, `SPUT`
- In showback mode only `Timestamp`, `AMID`, `ATYP`, `CNID`, `CSIZ`, `PATH`, `RSLT`, `RULE`, `SACC`, `SAIP`, `SBAC`, `SBAI`, `STAT`, `SUSR`, `TIME`, `TLIP` will be included. Notice how `S3KY` and `S3BK` (see the S3 PUT example above) are not included. That is on purpose (security and privacy), but obviously can be changed by you. `PATH` still contains some info that should probably be omitted when it's unnecessary for analytics purposes
- Only you know what fields are relevant and how much information should be added or removed to these reports

Run sg_audit_csv_converter.py from the data subdirectory against a decompressed audit log file in /sglogs. Save CSV output to sean-out.txt, debug info in debug.txt, and include a subset of rows and columns with `--data showback`:

```shell
./data/sg_audit_csv_converter.py /sglogs/audit.log sean-out.txt debug.txt --data showback
```

#### Sample [SGAC(CSV]) Output

It's just a CSV file with a bunch of rows and columns!

Comparison in source and destination file sizes (MB):

| audit.log | --data all  | --data showback |
|  :---:    |  :---:      |      :---:      |
|   18      |   11        |       5.2       |

#### Next Steps with [SGAC(CSV)] output

Slice it and dice that CSV file any way you see fit. Several simple examples:

- Plot cumulative egress from SGET (x axis is seconds, i.e. period of observation was short). This is for the all tenants but could by by tenant, by bucket, etc. The vertical line is a S3 PUT workload used to generate audit log data I needed for this project. Of course static, basic plots don't look very nice compared to Grafana but if you don't want those users access Grafana you can create PDF reports with tables and charts and email them to Tenants every now and then.

![SGAC-Egress-Plot](sgac/images/sgac_plot_cumulative_sget_egress_in_bytes.png)

- Import to a SQL DB and create reports. Example below shows combined SGET egress by tenant (STAT column). Notice how the sum, around 1.4 GB (in bytes), equals cumulative egress from the chart above

![SGAC-SGET-Egress-Cumulative-Sum-by-Tenant](sgac/images/sgac_sql_01.png)

- By tenant and their IP, for tenant's internal reference

![SGAC-SGET-Egress-Cumulative-Sum-by-Tenant](sgac/images/sgac_sql_02.png)

- By tenant accessing from non-local IPv4 addresses (the SG network is `10.128.0.0/16`), to calculate WAN egress from SGET traffic (as you can see the `"`s should be removed from the values in STAT and SBAC columns for easier SQL querying)

![SGAC-SGET-Egress-Cumulative-Sum-by-Tenant](sgac/images/sgac_sql_03.png)

#### Known issues and limitations

- Pyton converter script:
  - **IMPORTANT**: the script does not capture all audit messages
    - Except MTME in SDEL, SPUT, WDEL, WPUT, other [new codes in StorageGRID 11.5](https://docs.netapp.com/sgws-115/index.jsp?topic=%2Fcom.netapp.doc.sg-upgrade%2FGUID-32E18269-7337-471B-8CD1-CDDFB6E6603C.html) are not included (except MTME); this means all S3 Object Lock-related codes for SPUT (LKEN, LKLH, LKMD, LKRU), and CSIZ (Previous Object Size) in OVWR (Object Overwrite) may result in errors and require you to add them to the script
    - `MRSP` is one such entry. It contains a non-trivial JSON file which the script currently partially drops. You can easily find such rows with `cat audit.log | grep MRSP` and process them manually. Or better yet, fix the code and submit a pull request. It does not seem that partial or missing MRSP fields could impact showback analytics, but they could impact compliance analytics
  - While the Python script can output some debug info, it's not meant for reg-exp debugging - it's meant to catch failed KV pairs and usually tends to be empty (tested with an audit log from v11.5) because we drop `MRSP` (see above) values we cannot parse before that happens
    - How to check: compare the number of lines in audit.log with your output file. If output file has 10 lines less, that likely means 10 lines were dropped (e.g. maybe they contained `MRSP`)
  - Not all fields have "logical" values. Audit log may contain  `SGET` rows but with no `CSIZ` value, for example. [SGAC(CSV)] doesn't attempt to do anything about that

- R script:
  - Could work only with CSV generated in full mode, but has not been tested with updated Python script. If it doesn't work you can try an earlier version with input CSV generated by an older version of the Python script
  - May not cover all S3 messages (such as multi-part uploads, for example)

If you discover new keys (which is obvious from warnings or errors generated by the Python script) that are not supported or messages that cannot be parsed please submit a pull request.

#### Performance

- No meaningful testing or optimization has been done
- Based on a casual test with a 20 MB (decompressed size) log file, the Python script running on a notebook can process the log at 10 MB/s (35 GB/day). This can be paralellized by splitting decompressed log files or running several scripts against different time segments in the same file
- Performance comparison among these three tools is meaningless (they do different things) but since you must know, here's how they compare running against a 18 MB audit.log file:

| [SGAC(CSV)] | audit-explain  | audit-sum |
|  :---:    |  :---:    |  :---:    |
|   2s      |   0.7s    |  0.2s     |

#### Change Log

- 2021/06/24
  - Add details about management and access logs
  - Add one code (MTME) to the Python script

- 2020/11/03
  - Add SQL queries to illustrate reports that can be obtained from `showback`-mode CSV
  - Clarify more precisely about MRSP parsing

- 2020/11/02
  - Add `--data showback` option to extract to CSV a smaller subset of data and only rows related to main S3 and ILM operations

- 2020/11/01
  - Add about 10 new keys/fields that have appeared since the original Python script was released
  - Silently drop MRSP key-value pairs because the script cannot handle them
  - Add debug_file argument for issues (except MRSP) with log parsing
  - Minor changes to the script
