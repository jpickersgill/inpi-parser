# inpi-parser
Python pipeline designed to download newly published French patent applications from the 'Brevets français – Notices bibliographiques' INPI FTP server and comprehensively parse them.  

Patents are stored in the server individually in XML files bundled into ZIP archives. They are uploaded on a weekly basis. This pipeline:  

1. downloads weekly `FRNEW` archives according to user selection of desired period;
2. extracts the XML files;
3. parses the available bibliographic and legal-status information;
4. exports the resulting relational tables as CSV files
  
Refer to the data dictionary for more complete descriptions of the output tables and variables. 

## Scope
This version processes `FRNEW` files, which contain information about newly published French patent applications during a given week. It does not process `FRAMD` which concerns post-application events such as grants, search-report publications, register entries, lapses & corrections. The resulting data therefore describe patent applications at the moment of publication.

## Requirements
- Python 3
- pandas
- INPI FTP credentials  

Most packages are covered by Python's standard library.

## Running the code
### FTP access
The code requires a (free) license to access the FTP server. You can obtain a log-in by completing [this formulaire](https://www.inpi.fr/sites/default/files/2026-02/formulaire%20de%20cr%C3%A9ation%20de%20compte_V16_R.pdf) and submitting it to licenses@inpi.fr. [Refer here](https://data.inpi.fr/content/editorial/lien-serveur-ftp-PI) for more information.

Once you have gained your log-in credentials, run this code (substituting your username and password for `your_username` and `your_password` in your macOS or Linus terminal:  
```
export INPI_FTP_USERNAME="your_username"  
export INPI_FTP_PASSWORD="your_password"
```

Or this in Windows Powershell:  
```
$env:INPI_FTP_USERNAME="your_username"  
$env:INPI_FTP_PASSWORD="your_password"
```

Credentials must be re-entered with every new terminal session.  

It is not recommended to add your provided username and password into the python files directly for security reasons. Please do not commit credentials to GitHub, place them in source code, or in screenshots of example output. These credentials are confidential and may not be shared or transferred.  

### Python pipeline
Clone or download this repository and ensure the following scripts are in the same folder:
`download_patents.py`
`audit_patent_xml.py`
`parse_patents.py`
`run_pipeline.py`

From that folder, run: `python run_pipeline.py` (or `python3 run_pipeline.py`, depending on configuration).  

The programme will ask for a starting year and week and an ending year and week (to select the period for which you want to inspect patents). It will then download, extract, and parse all available FRNEW archives within that interval.  

*Note: `audit_patent_xml.py` was developed to scan all available patents (from 2017 - 2026) and build a parser (parse_patents.py) that was as comprehensive as possible. It is not necessary to run it again for the script to work, but you may do so for your own interest.*

## Generated folders
The pipeline creates:

```text
1. patent_downloads/   Downloaded weekly ZIP archives
2. patent_xml/         Extracted XML files
3. patent_outputs/     Parsed CSV tables
```  
These folders are excluded from version control as the underlying files can be large and may be reproduced by rerunning the pipeline.  

The script does not automatically remove files from earlier runs; if `patent_xml/` already contains XML files from a previously-request interval, those files will also be included in the next parsing run.

## Output tables
`patents.csv` contains one row per patent publication.

The remaining tables contain information that can have multiple records per patent:
- `citations.csv`
- `classifications.csv`
- `parties.csv`
- `priorities.csv`
- `publication_references.csv`
- `related_documents.csv`

Each table can be linked to `patents.csv` using `publication_number`.  

This pipeline also produces:
- `parser_errors.csv` to record malformed XML files;
- `skipped_non_patent_files.csv` to record package indexes and other non-patent XML files

## Data source
Data are provided by the French National Institute of Industrial Property (INPI) through its property-industrial-data FTP service. Users are responsible for complying with the applicable INPI data-reuse licence and requirements concerning personal data.
