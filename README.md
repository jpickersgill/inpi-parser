# inpi-parser
Python code designed to download newly published French patent applications from the 'Brevets français – Notices bibliographiques' INPI FTP server and comprehensively scrape them.  

Patents are stored in the server individually in .xml files. They are uploaded on a weekly basis. This script downloads them, scrapes them, and stores them in a series of .csv files *(refer to the data dictionary for more complete descriptions of the contents)*.  

## Running the code
### FTP access
The code requires a license to access the FTP server. You can obtain a log-in by completing [this formulaire](https://www.inpi.fr/sites/default/files/2026-02/formulaire%20de%20cr%C3%A9ation%20de%20compte_V16_R.pdf) and submitting it to licenses@inpi.fr. Access is free, and you may [refer here](https://data.inpi.fr/content/editorial/lien-serveur-ftp-PI) for more information.

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
Download all four python scripts into the same folder: download_patents.py, audit_patent_xml.py, parse_patents.py, & run_pipeline.py.  

Execute run_pipeline.py.  

*Note: audit_patent_xml.py was developed to scan all available patents (from 2017 - 2026) and build a parser (parse_patents.py) that was as comprehensive as possible. It is not necessary to run it again for the script to work, but you may do so for your own interest.*

## Output .csv organisation
The **patents.csv** file contains one row per patent. All others *(citations.csv, classifications.csv, inscriptions.csv, parties.csv, priorities.csv, publication_references.csv, related_documents.csv)* contain information which (occasionally) involves multiple entries per patent, and hence they record multiple rows per patent.
