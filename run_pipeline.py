from pathlib import Path
from download_patents import download_and_extract
from parse_patents import parse_all_patents
# from audit_patent_xml import audit_patent_xml

def main():
    base_dir = Path(__file__).resolve().parent

    download_dir = base_dir / "patent_downloads"
    extract_dir = base_dir / "patent_xml"
    output_dir = base_dir / "patent_outputs"
    # audit_output_dir = base_dir / "audit_outputs"

    download_and_extract(
        download_dir=download_dir,
        extract_dir=extract_dir
    )

    # The xml schema audit was used to design the parser
    # It's not necessary to run it again for the code to work
    # audit_patent_xml(
    #     extract_dir=extract_dir,
    #     output_dir=audit_output_dir
    # )

    parse_all_patents(
        extract_dir=extract_dir,
        output_dir=output_dir
    )

    print("Pipeline complete")

if __name__ == "__main__":
    main()