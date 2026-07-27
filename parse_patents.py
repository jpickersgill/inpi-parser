from pathlib import Path                        #Create path objects
import xml.etree.ElementTree as ET              #Python XML parser
import pandas as pd                             #Working with data in rows & columns

#-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-~-~-#
# Step 5: Parse .xml files and build desired data frames #
#-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~--~-~-~-~-~--~-~-~-~-~-~-#
#much code for many fields

def clean_tag(tag):
    return tag.split("}",1)[-1]

def parse_patent(xml_path, root):
    bibliographic_data = root.find("fr-bibliographic-data")

    #Some helpers to reduce repetition in the following code
    def safe_findtext(parent, tag):
        if parent is None:
            return None
        return parent.findtext(tag)

    def safe_get(element, attribute):
        if element is None:
            return None
        return element.get(attribute)

    def safe_find(parent, path):
        if parent is None:
            return None
        return parent.find(path)

    def safe_all_text(element):
        if element is None:
            return None
        return " ".join("".join(element.itertext()).split())

    classification_records = []
    ipc_texts = []
    priority_records = []
    publication_reference_records = []
    related_document_records = []
    inscription_records = []

    ipc_classifications = bibliographic_data.findall("classifications-ipcr/classification-ipcr")
    for classification in ipc_classifications:
        raw_text = classification.findtext("text")

        if raw_text is not None:
            cleaned_text = " ".join(raw_text.split())
            ipc_texts.append(cleaned_text)
            classification_record = {
                "publication_number": root.get("doc-number"),
                "classification_type": "IPC",
                "sequence": classification.get("sequence"),
                "classification_text": cleaned_text
            }
            classification_records.append(classification_record)

    detailed_classifications = bibliographic_data.findall("patent-classifications/patent-classification")

    for classification in detailed_classifications:
        classification_scheme = safe_find(classification,"classification-scheme")
        action_date = safe_find(classification, "action-date")

        classification_record = {
            "publication_number": root.get("doc-number"),
            "classification_type": (safe_get(classification_scheme, "scheme") or "DETAILED"),
            "sequence": classification.get("sequence"),
            "classification_text": None,
            "classification_symbol": safe_findtext(classification, "classification-symbol"),
            "classification_scheme": safe_get(classification_scheme, "scheme"),
            "classification_scheme_office": safe_get(classification_scheme, "office"),
            "classification_scheme_date": safe_findtext(classification_scheme, "date"),
            "classification_value": safe_findtext(classification, "classification-value"),
            "classification_status": safe_findtext(classification, "classification-status"),
            "classification_data_source": safe_findtext(classification, "classification-data-source"),
            "symbol_position": safe_findtext(classification, "symbol-position"),
            "action_date": safe_findtext(action_date,"date")
        }

        classification_records.append(classification_record)

    priority_claims = bibliographic_data.findall("fr-priority-claims/fr-priority-claim")
    for priority in priority_claims:
        priority_record = {
            "publication_number": root.get("doc-number"),
            "priority_sequence": priority.get("sequence"),
            "priority_country": safe_findtext(priority, "country"),
            "priority_document_number": safe_findtext(priority, "doc-number"),
            "priority_kind": safe_findtext(priority, "kind"),
            "priority_date": safe_findtext(priority, "date")
        }
        priority_records.append(priority_record)

    related_document_paths = [
        ("parent", "related-documents/division/parent-doc"),
        ("child", "related-documents/division/child-doc")
        ]

    for relationship_type, relationship_path in related_document_paths:
        related_documents = bibliographic_data.findall(relationship_path)

        for relationship_sequence, related_document in enumerate(
            related_documents,
            start=1
        ):
            related_document_id = safe_find(
                related_document,
                "document-id"
            )

            related_document_record = {
                "publication_number": root.get("doc-number"),
                "relationship_type": relationship_type,
                "relationship_sequence": relationship_sequence,
                "related_country": safe_findtext(related_document_id, "country"),
                "related_document_number": safe_findtext(related_document_id, "doc-number"),
                "related_date": safe_findtext(related_document_id, "date")
            }

            related_document_records.append(related_document_record)

    inscriptions = root.findall("fr-patent-life/fr-inscription")
    for inscription_sequence, inscription in enumerate(
        inscriptions,
        start=1
    ):
        inscription_record = {
            "publication_number": root.get("doc-number"),
            "inscription_sequence": inscription_sequence,
            "inscription_date": safe_findtext(inscription, "date"),
            "inscription_bopi": safe_findtext(inscription, "fr-bopinum"),
            "inscription_code": safe_findtext(inscription, "fr-code-inscription"),
            "inscription_nature": safe_findtext(inscription, "fr-nature-inscription"),
            "registered_number": safe_findtext(inscription, "registered-number")
        }

        inscription_records.append(inscription_record)
    
    last_fee_payment = root.find("fr-patent-life/fr-date-availability/fr-last-fee-payement")
    next_fee_payment = root.find("fr-patent-life/fr-date-availability/fr-next-fee-payement")
    search_completed = root.find("fr-patent-life/fr-date-availability/fr-date-search-completed")

    application_refused = root.find("fr-patent-life/fr-date-availability/fr-date-application-refused")
    grant = root.find("fr-patent-life/fr-date-availability/fr-date-granted")
    lapsed = root.find("fr-patent-life/fr-date-availability/fr-date-lapsed")
    notification_lapsed = root.find("fr-patent-life/fr-date-availability/fr-date-notification-lapsed")
    supplemental_search = root.find("fr-patent-life/fr-date-availability/fr-date-search-supplemental")

    patent_status = root.find("fr-patent-life/fr-status-list/fr-status")
    errata = root.find("fr-patent-life/fr-erratas/fr-errata")

    grant_document_id = safe_find(grant, "document-id")
    extension = safe_find(bibliographic_data, "fr-extension")
    amended_claim = root.find("fr-patent-life/fr-amended-claim")

    publication_references = bibliographic_data.findall("fr-publication-data/fr-publication-reference")
    for reference_sequence, reference in enumerate(
        publication_references,
        start=1
    ):
        reference_document_id = safe_find(reference, "document-id")
        publication_reference_record = {
            "publication_number": root.get("doc-number"),
            "reference_sequence": reference_sequence,
            "data_format": safe_get(reference, "data-format"),
            "reference_country": safe_findtext(reference_document_id, "country"),
            "reference_document_number": safe_findtext(reference_document_id, "doc-number"),
            "reference_kind": safe_findtext(reference_document_id, "kind"),
            "reference_date": safe_findtext(reference_document_id, "date"),
            "reference_bopi": safe_findtext(reference, "fr-bopinum"),
            "reference_nature": safe_findtext(reference, "fr-nature")
        }

        publication_reference_records.append(publication_reference_record)

    publication_reference = bibliographic_data.find("fr-publication-data/fr-publication-reference[@data-format='inpi']")
    if publication_reference is None:
        publication_reference = safe_find(bibliographic_data, "fr-publication-data/fr-publication-reference")

    publication_document_id = safe_find(publication_reference, "document-id")

    application_reference = bibliographic_data.find("fr-application-reference[@data-format='inpi']")
    if application_reference is None:
        application_reference = bibliographic_data.find("fr-application-reference")

    application_document_id = safe_find(application_reference, "document-id")
    application_docdb_reference = bibliographic_data.find("fr-application-reference[@data-format='docdb']")
    application_docdb_document_id = safe_find(application_docdb_reference, "document-id")

    title_element = safe_find(bibliographic_data, "invention-title")
    abstract_element = safe_find(root, "abstract")

    patent_record = {
        #file provenance
        "source_file": str(xml_path),

        #root attributes
        "publication_number": root.get("doc-number"),
        "family_id": root.get("family-id"),
        "country": root.get("country"),
        "kind": root.get("kind"),
        "status": root.get("status"),
        "document_id": root.get("id"),
        "date_produced": root.get("date-produced"),
        "dtd_version": root.get("dtd-version"),
        "document_language": root.get("lang"),

        #publication info
        "publication_data_format": safe_get(publication_reference, "data-format"),
        "publication_country": safe_findtext(publication_document_id, "country"),
        "publication_kind": safe_findtext(publication_document_id, "kind"),
        "publication_date": safe_findtext(publication_document_id, "date"),
        "publication_bopi": safe_findtext(publication_reference, "fr-bopinum"),
        "publication_nature": safe_findtext(publication_reference, "fr-nature"),

        #application info
        "application_data_format": safe_get(application_reference, "data-format"),
        "application_doc_id": safe_get(application_reference, "doc-id"),
        "application_country": safe_findtext(application_document_id, "country"),
        "application_number": safe_findtext(application_document_id, "doc-number"),
        "application_date": safe_findtext(application_document_id, "date"),
        "application_kind": safe_findtext(application_document_id, "kind"),
        "application_docdb_country": safe_findtext(application_docdb_document_id, "country"),
        "application_docdb_number": safe_findtext(application_docdb_document_id, "doc-number"),
        "application_docdb_date": safe_findtext(application_docdb_document_id, "date"),
        "application_docdb_kind": safe_findtext(application_docdb_document_id, "kind"),

        #patent info
        "title": safe_all_text(title_element),
        "title_language": safe_get(title_element, "lang"),
        "abstract": safe_all_text(abstract_element),
        "abstract_language": safe_get(abstract_element, "lang"),
        "filing_language": safe_findtext(bibliographic_data, "language-of-filing"),
        "ipc_classifications": "; ".join(ipc_texts),
        "extension_territory": safe_findtext(extension, "fr-extension-territory"),
        "amended_claim": safe_all_text(amended_claim),

        #patent life info
        "last_fee_payment_date": safe_findtext(last_fee_payment, "date"),
        "last_fee_payment_percentile": safe_get(last_fee_payment, "percentile"),
        "next_fee_payment_date": safe_findtext(next_fee_payment, "date"),
        "next_fee_payment_percentile": safe_get(next_fee_payment, "percentile"),
        "search_completed_date": safe_findtext(search_completed, "date"),
        "search_completed_bopi": safe_findtext(search_completed, "fr-bopinum"),
        "application_refused_date": safe_findtext(application_refused,"date"),
        "grant_date": safe_findtext(grant_document_id, "date"),
        "grant_country": safe_findtext(grant_document_id, "country"),
        "grant_number": safe_findtext(grant_document_id, "doc-number"),
        "grant_kind": safe_findtext(grant_document_id, "kind"),
        "grant_bopi": safe_findtext(grant, "fr-bopinum"),
        "lapsed_date": safe_findtext(lapsed, "date"),
        "notification_lapsed_date": safe_findtext(notification_lapsed, "date"),
        "notification_lapsed_bopi": safe_findtext(notification_lapsed, "fr-bopinum"),
        "supplemental_search_date": safe_findtext(supplemental_search, "date"),
        "supplemental_search_bopi": safe_findtext(supplemental_search, "fr-bopinum"),
        "status_nature": safe_findtext(patent_status, "fr-nature"),
        "status_language": safe_get(patent_status, "lang"),
        "errata_date": safe_findtext(errata, "date"),
        "errata_bopi": safe_findtext(errata, "fr-bopinum"),
        "errata_text": safe_findtext(errata, "text")
    }

    party_records = []

    def make_party_record(party, role):
        addressbook = party.find("addressbook")
        if addressbook is not None:
            address = addressbook.find("address")
        else:
            address = None

        party_record = {
            "publication_number": root.get("doc-number"),
            "role": role,
            "sequence": party.get("sequence"),

            #role-specific info
            "designation": safe_get(party, "designation"),
            "applicant_type": safe_get(party, "app-type"),
            "representative_type": safe_get(party, "rep-type"),
            "data_format": safe_get(party, "data-format"),

            #person or organisation info
            "first_name": safe_findtext(addressbook, "first-name"),
            "last_name": safe_findtext(addressbook, "last-name"),
            "organisation_name": safe_findtext(addressbook, "orgname"),
            "iid": safe_findtext(addressbook, "iid"),

            #address info
            "address_language": safe_get(addressbook, "lang"),
            "address_1": safe_findtext(address, "address-1"),
            "city": safe_findtext(address, "city"),
            "postcode": safe_findtext(address, "postcode"),
            "country": safe_findtext(address, "country")
        }

        return party_record

    applicants = bibliographic_data.findall(
        "parties/applicants/applicant"
    )
    for applicant in applicants:
        party_records.append(
            make_party_record(applicant, "applicant")
        )

    inventors = bibliographic_data.findall(
        "parties/inventors/inventor"
    )
    for inventor in inventors:
        party_records.append(
            make_party_record(inventor, "inventor")
        )

    agents = bibliographic_data.findall(
        "parties/agents/agent"
    )
    for agent in agents:
        party_records.append(
            make_party_record(agent, "agent")
        )

    owners = bibliographic_data.findall(
        "fr-owners/fr-owner"
    )
    for owner in owners:
        party_records.append(
            make_party_record(owner, "owner")
        )

    citation_records = []

    citations = root.findall(
        "fr-patent-life/references-cited/citation"
    )

    for citation_sequence, citation in enumerate(citations, start=1):
        patent_citation = citation.find("patcit")
        non_patent_citation = citation.find("nplcit")

        if patent_citation is not None:
            document_id = patent_citation.find("document-id")

            citation_record = {
                "publication_number": root.get("doc-number"),
                "citation_sequence": citation_sequence,
                "citation_type": "patent",
                "citation_text": safe_findtext(
                    patent_citation,
                    "text"
                ),
                "cited_country": safe_findtext(
                    document_id,
                    "country"
                ),
                "cited_document_number": safe_findtext(
                    document_id,
                    "doc-number"
                ),
                "cited_date": safe_findtext(
                    document_id,
                    "date"
                )
            }

        elif non_patent_citation is not None:
            citation_record = {
                "publication_number": root.get("doc-number"),
                "citation_sequence": citation_sequence,
                "citation_type": "non_patent_literature",
                "citation_text": safe_findtext(
                    non_patent_citation,
                    "text"
                ),
                "cited_country": None,
                "cited_document_number": None,
                "cited_date": None
            }

        else:
            citation_record = {
                "publication_number": root.get("doc-number"),
                "citation_sequence": citation_sequence,
                "citation_type": "unknown",
                "citation_text": safe_all_text(citation),
                "cited_country": None,
                "cited_document_number": None,
                "cited_date": None
            }

        citation_records.append(citation_record)

    return (
        patent_record,
        party_records,
        classification_records,
        citation_records,
        priority_records,
        publication_reference_records,
        related_document_records,
        inscription_records
    )

def parse_all_patents(extract_dir, output_dir):
    extract_dir = Path(extract_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    xml_files = list(extract_dir.glob("**/*.xml"))

    patent_records = []
    party_records = []
    classification_records = []
    citation_records = []
    priority_records = []
    publication_reference_records = []
    related_document_records = []
    inscription_records = []

    parse_errors = []
    skipped_files = []

    for xml_path in xml_files:
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError as error:
            parse_errors.append({
                "source_file": str(xml_path),
                "error": str(error)
            })
            continue

        root_tag = clean_tag(root.tag)
        if root_tag != "fr-patent-document":
            skipped_files.append({
                "source_file": str(xml_path),
                "root_tag": root_tag,
                "reason": "Not a patent document"
            })
            continue

        if root.find("fr-bibliographic-data") is None:
            skipped_files.append({
                "source_file": str(xml_path),
                "root_tag": root_tag,
                "reason": "Missing fr-bibliographic-data"
            })
            continue

        (patent_record,
        patent_parties,
        patent_classifications,
        patent_citations,
        patent_priorities,
        patent_publication_references,
        patent_related_documents,
        patent_inscriptions
        ) = parse_patent(xml_path, root)

        patent_records.append(patent_record)
        party_records.extend(patent_parties)
        classification_records.extend(patent_classifications)
        citation_records.extend(patent_citations)
        priority_records.extend(patent_priorities)
        publication_reference_records.extend(patent_publication_references)
        related_document_records.extend(patent_related_documents)
        inscription_records.extend(patent_inscriptions)

    patents_df = pd.DataFrame(patent_records)
    parties_df = pd.DataFrame(party_records)
    classifications_df = pd.DataFrame(classification_records)
    citations_df = pd.DataFrame(citation_records)
    parse_errors_df = pd.DataFrame(parse_errors, columns=["source_file", "error"])
    skipped_files_df = pd.DataFrame(skipped_files, columns=["source_file", "root_tag", "reason"])
    priorities_df = pd.DataFrame(priority_records)
    publication_references_df = pd.DataFrame(publication_reference_records)
    related_documents_df = pd.DataFrame(related_document_records)
    inscriptions_df = pd.DataFrame(inscription_records)

    patents_df.to_csv(output_dir/"patents.csv", index=False)
    parties_df.to_csv(output_dir/"parties.csv", index=False)
    classifications_df.to_csv(output_dir/"classifications.csv", index=False)
    citations_df.to_csv(output_dir/"citations.csv", index=False)
    parse_errors_df.to_csv(output_dir/"parser_errors.csv", index=False)
    skipped_files_df.to_csv(output_dir/"skipped_non_patent_files.csv", index=False)
    priorities_df.to_csv(output_dir/"priorities.csv", index=False)
    publication_references_df.to_csv(output_dir/"publication_references.csv", index=False)
    related_documents_df.to_csv(output_dir/"related_documents.csv", index=False)
    inscriptions_df.to_csv(output_dir/"inscriptions.csv", index=False)

    print(f"Parsed {len(patents_df)} patent files")
    print(f"Results saved in: {output_dir}")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    parse_all_patents(
        extract_dir=base_dir / "patent_xml",
        output_dir=base_dir / "patent_outputs"
    )