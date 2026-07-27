from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
import pandas as pd

def audit_patent_xml(extract_dir, output_dir):
    extract_dir = Path(extract_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    xml_files = list(extract_dir.glob("**/*.xml"))

#-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-~-~-~#
# Step 3: audit XML schema for unparsed data and variants #
#-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-~-~-~#

    element_counts = Counter()                  # Total # of times each XML path appears
    element_files = defaultdict(set)            # Which files contain each path
    element_text_counts = Counter()             # How often each path contains text
    element_text_examples = {}                  # One example of that text

    attribute_counts = Counter()                # How often each attribute appears
    attribute_files = defaultdict(set)          # Which files contain each attribute
    attribute_examples = {}                     # One example value

    file_path_counts = Counter()                # Occurrences of each path within each file
    parse_errors = []                           # XML files that fail to parse
    patent_file_count = 0                       # Count only XML files with fr-patent-document as root
    non_patent_files = []                       # Record non-patent XML files (e.g., package index)

    #Example: <applicant sequence="1">Jane Doe</applicant>
        #Element (whole XML item): <applicant sequence="1">Jane Doe</applicant>
        #Tag (element name): applicant
        #Attribute (additional info within opening tag): sequence="1"
        #Text (content within element): Jane Doe

    def clean_tag(tag):
        return tag.split("}", 1)[-1]            #Defining tags within XML angle brackets

    def audit_element(element, parent_path, source_file):   #Main auditing function: looking for all possible elements, tags, and attributes across all .xml files
        tag = clean_tag(element.tag)

        if parent_path:
            current_path = f"{parent_path}/{tag}"
        else:
            current_path = tag

        element_counts[current_path] += 1                        #Start counting from 1
        element_files[current_path].add(source_file)
        file_path_counts[(source_file, current_path)] += 1

        text = " ".join((element.text or "").split())
        if text:
            element_text_counts[current_path] +=1
            if current_path not in element_text_examples:
                element_text_examples[current_path] = text[:300]

        for attribute_name, attribute_value in element.attrib.items():
            attribute_name = clean_tag(attribute_name)
            attribute_key = (current_path, attribute_name)
            attribute_counts[attribute_key] += 1
            attribute_files[attribute_key].add(source_file)
            if attribute_key not in attribute_examples:
                attribute_examples[attribute_key] = attribute_value

        for child in element:                                   #Recursive function looking through all children of the XML tree
            audit_element(
                child,
                current_path,
                source_file
            )

    for xml_path in xml_files:
        try:
            root = ET.parse(xml_path).getroot()
            root_tag = clean_tag(root.tag)
            if root_tag != "fr-patent-document":
                non_patent_files.append({
                    "source_file": str(xml_path),
                    "root_tag": root_tag
                })
                continue
            patent_file_count += 1

            try:
                source_file = str(xml_path.relative_to(extract_dir))
            except ValueError:
                source_file = str(xml_path)

            audit_element(
                root,
                parent_path="",
                source_file=source_file
            )

        except ET.ParseError as error:
            parse_errors.append({
                "source_file": str(xml_path),
                "error": str(error)
            })

    element_rows = []
    for element_path in sorted(element_counts):
        occurrences_by_file = [
            count 
            for (source_file, path), count in file_path_counts.items()
            if path == element_path
        ]

        minimum_per_file = min(occurrences_by_file)
        if len(element_files[element_path]) < patent_file_count:
            minimum_per_file = 0

        element_rows.append({
            "element_path": element_path,
            "total_occurrences": element_counts[element_path],
            "files_present": len(element_files[element_path]),
            "nonempty_text_occurrences": element_text_counts[element_path],
            "minimum_per_file": minimum_per_file,
            "maximum_per_file": max(occurrences_by_file),
            "example_text": element_text_examples.get(element_path)
        })

    attribute_rows = []
    for element_path, attribute_name in sorted(attribute_counts):
        attribute_key = (element_path, attribute_name)
        attribute_rows.append({
            "element_path": element_path,
            "attribute_name": attribute_name,
            "total_occurrences": attribute_counts[attribute_key],
            "files_present": len(attribute_files[attribute_key]),
            "example_value": attribute_examples.get(attribute_key)
        })

    schema_elements_df = pd.DataFrame(element_rows)
    schema_attributes_df = pd.DataFrame(attribute_rows)
    schema_errors_df = pd.DataFrame(parse_errors, columns=["source_file", "error"])
    non_patent_files_df = pd.DataFrame(non_patent_files, columns=["source_file", "root_tag"])

    schema_elements_df.to_csv(output_dir/"xml_schema_elements.csv", index=False)
    schema_attributes_df.to_csv(output_dir/"xml_schema_attributes.csv", index=False)
    schema_errors_df.to_csv(output_dir/"xml_schema_errors.csv", index=False)
    non_patent_files_df.to_csv(output_dir/"xml_schema_non_patent_files.csv", index=False)

    print(f"Found {len(schema_elements_df)} unique XML element paths")
    print(f"Found {len(schema_attributes_df)} unique XML path-attribute combinations")
    print(f"XML parse errors: {len(schema_errors_df)}")

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-#
    # Step 4: organise schema audit results for database design #
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-#

    repeating_elements_df = schema_elements_df[
        schema_elements_df["maximum_per_file"] > 1                  #Did any elements occur more than once in a single file?
    ].sort_values(
        by=["maximum_per_file", "element_path"],
        ascending=[False,True]
    )

    optional_elements_df = schema_elements_df[
        schema_elements_df["files_present"] < patent_file_count        #Did any elements appear in fewer than all files?
    ].sort_values(
        by=["files_present", "element_path"]
    )

    repeating_elements_df.to_csv(output_dir/"xml_schema_repeating_elements.csv", index=False)
    optional_elements_df.to_csv(output_dir/"xml_schema_optional_elements.csv", index=False)

    print(f"Successfully audited patent files: {patent_file_count}")
    print(f"Skipped non-patent XML files: {len(non_patent_files_df)}")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent

    audit_patent_xml(
        extract_dir=base_dir / "patent_xml",
        output_dir=base_dir / "audit_outputs"
    )