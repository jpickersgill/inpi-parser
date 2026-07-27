import os

from ftplib import FTP                          #Establish access to INPI FTP server
from pathlib import Path                        #Create path objects
from zipfile import ZipFile                     #Read and write zip files

#-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-#
# Step 1: Download patent files from INPI FTP server #
#-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-#

HOST = "www.inpi.net"

def download_and_extract(download_dir, extract_dir):
    username = os.environ["INPI_FTP_USERNAME"]
    password = os.environ["INPI_FTP_PASSWORD"]

    download_dir = Path(download_dir)
    extract_dir = Path(extract_dir)

    download_dir.mkdir(parents=True, exist_ok=True)    
    extract_dir.mkdir(parents=True, exist_ok=True)             

    with FTP(HOST, timeout=30) as ftp:
        ftp.login(user=username, passwd=password)
        print("Connection successful")
        print("Current directory:", ftp.pwd())          

        remote_names = ftp.nlst()                       
        frnew_files = [
            name for name in remote_names
            if "FRNEW" in name.upper() and name.lower().endswith(".zip")    #Looks for new patent .zip files only (ignoring patent amendments)
        ]
        print(f"Found {len(frnew_files)} FRNEW .zip files")                 #Using len because frnew_files is a list and len counts the length of a list!

        for filename in frnew_files[:10]:                                   #Checks the right files are being called (final number refers to the week of the year - FR_FRNEWST36_2026_01.zip contains patents published in the first week of 2026)
            print(filename)

        year_folders = [
            name for name in remote_names
            if name.isdigit() and len(name) == 4
        ]
        print(year_folders)                                                 #Years 2017-2025 have their own folders, 2026 data is loose in / directory

        ftp.cwd("/")
        all_frnew_files = frnew_files.copy()                                #frnew_files contains 2026 (or most recent year, unfiled) data, we will backfill the data into the copy

        for year in year_folders:
            ftp.cwd(f"/{year}")
            year_names = ftp.nlst()
            year_frnew = [
                name for name in year_names
                if "FRNEW" in name.upper() and name.lower().endswith(".zip")
            ]
            for name in year_frnew:
                all_frnew_files.append(f"{year}/{name}")                   #Collates all FRNEW files, sorts them into a directory of year -> file name

        all_frnew_files.sort()
        print(f"Found {len(all_frnew_files)} total FRNEW .zip files")
        for path in all_frnew_files[:10]:
            print(path)
                                
        start_year = int(input("Start year: "))                             #To filter data download by years and weeks (1-52)
        start_week = int(input("Start week: "))
        end_year = int(input("End year: "))
        end_week = int(input("End week: "))

        selected_files = []
        for path in all_frnew_files:
            filename = path.split("/")[-1]
            parts = filename.split("_")
            file_year = int(parts[2])
            file_week = int(parts[3].replace(".zip",""))
            if (start_year, start_week) <= (file_year, file_week) <= (end_year, end_week):
                selected_files.append(path)                                #Retrieve only the desired files within the chosen range
        print(f"Selected {len(selected_files)} files")                     #How many files are in the chosen range?
        for path in selected_files[:10]:
            print(path)                                                    #First 10 files (check: do they match the beginning of the chosen range?)

        ftp.cwd("/")
        for remote_path in selected_files:
            local_path = download_dir / Path(remote_path).name
            with local_path.open("wb") as local_file:
                ftp.retrbinary(f"RETR {remote_path}", local_file.write)    #Download selected files within chosen range
            print(f"Downloaded: {local_path}")                             #Check names of downloaded files


    #-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-~-~-~-~-~-~-#
    # Step 2: Extract .zip files and organise .xml files for parsing #
    #-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-~-~-~-~-~-~-#

    zip_files = [
        download_dir / Path(remote_path).name
        for remote_path in selected_files
    ]
    print(f"Found {len(zip_files)} .zip files to extract")

    for zip_path in zip_files:
        with ZipFile(zip_path, "r") as archive:
            xml_names = [
                name for name in archive.namelist()
                if name.lower().endswith(".xml")
            ]
            print(f"Found {len(xml_names)} .xml files (patents)")

            for xml_name in xml_names:
                archive.extract(xml_name, extract_dir)
        print(f"Extracted {len(xml_names)} .xml files (patents) from {zip_path.name}")

    print("Download and extraction complete")
    return extract_dir

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent

    download_and_extract(
        download_dir=base_dir / "patent_downloads",
        extract_dir=base_dir / "patent_xml"
    )