from transformers import AutoTokenizer, AutoModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import numpy as np
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_embeddings(texts, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """Generate embeddings using transformers library directly."""
    try:
        # For now, let's use a simple TF-IDF approach since PyTorch isn't compatible
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
        embeddings = vectorizer.fit_transform(texts).toarray()
        
        return embeddings, vectorizer
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        return None, None

def setup_legal_document_database():
    """Set up the legal document database with vector embeddings."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        logger.info("Initializing embedding system...")
        
        # Sample legal documents with more comprehensive content - 50+ records
        legal_docs = [
            # Civil Procedure
            {
                "id": "doc1", 
                "title": "Civil Procedure Code - Section 14B",
                "text": "In accordance with section 14B of the Civil Procedure Code, all proceedings must be conducted in accordance with established legal precedent. This section specifically addresses the requirements for proper notice and due process in civil litigation matters. Courts must ensure that all parties receive adequate notification of proceedings and have sufficient opportunity to present their case.",
                "category": "civil_procedure",
                "jurisdiction": "federal"
            },
            {
                "id": "doc2",
                "title": "Federal Rules of Civil Procedure - Rule 12",
                "text": "Rule 12 of the Federal Rules of Civil Procedure governs defenses and objections, including motions to dismiss. A motion to dismiss for failure to state a claim upon which relief can be granted must be filed before answering the complaint. The court must accept all factual allegations in the complaint as true and draw all reasonable inferences in favor of the plaintiff when evaluating such motions.",
                "category": "civil_procedure",
                "jurisdiction": "federal"
            },
            {
                "id": "doc3",
                "title": "Discovery Rules - Electronic Evidence",
                "text": "Electronic discovery rules require parties to preserve, search, and produce electronically stored information (ESI) in litigation. Parties must meet and confer regarding the scope of discovery, search terms, and file formats. Failure to preserve relevant electronic evidence can result in sanctions including adverse inference instructions to the jury.",
                "category": "civil_procedure",
                "jurisdiction": "federal"
            },
            
            # Housing/Landlord-Tenant Law
            {
                "id": "doc4", 
                "title": "Landlord-Tenant Law - Eviction Notice",
                "text": "The landlord must give a 30-day notice prior to eviction proceedings for month-to-month tenancies. This notice must be in writing and must specify the grounds for eviction as outlined in applicable state housing laws. The notice period may vary depending on the jurisdiction and the reason for eviction, such as non-payment of rent or lease violations.",
                "category": "housing_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc5",
                "title": "Security Deposit Regulations",
                "text": "State security deposit laws limit the amount landlords can charge as security deposits, typically one to two months' rent. Landlords must return security deposits within a specified timeframe after lease termination, usually 14-30 days, along with an itemized statement of any deductions for damages beyond normal wear and tear.",
                "category": "housing_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc6",
                "title": "Habitability Standards and Warranty",
                "text": "The implied warranty of habitability requires landlords to maintain rental properties in livable condition. This includes ensuring proper heating, plumbing, electrical systems, and structural integrity. Tenants may have the right to withhold rent or terminate the lease if the landlord fails to address serious habitability issues within a reasonable time.",
                "category": "housing_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc7",
                "title": "Fair Housing Act Compliance",
                "text": "The Fair Housing Act prohibits discrimination in housing based on race, color, religion, sex, national origin, familial status, or disability. Landlords cannot refuse to rent, set different terms, or provide different services based on these protected characteristics. Reasonable accommodations must be made for tenants with disabilities.",
                "category": "housing_law",
                "jurisdiction": "federal"
            },
            
            # Contract Law
            {
                "id": "doc8",
                "title": "Contract Law - Formation Requirements",
                "text": "A valid contract requires offer, acceptance, consideration, and mutual assent. All parties must have legal capacity to enter into the agreement, and the contract terms must be sufficiently definite and certain. The offer must be communicated to the offeree, and acceptance must be unequivocal and in accordance with the terms of the offer.",
                "category": "contract_law",
                "jurisdiction": "common_law"
            },
            {
                "id": "doc9",
                "title": "Statute of Frauds Requirements",
                "text": "Certain contracts must be in writing to be enforceable under the Statute of Frauds, including contracts for the sale of land, contracts that cannot be performed within one year, and contracts for the sale of goods over $500. The writing must identify the parties, subject matter, and essential terms, and be signed by the party to be charged.",
                "category": "contract_law",
                "jurisdiction": "common_law"
            },
            {
                "id": "doc10",
                "title": "Breach of Contract Remedies",
                "text": "When a contract is breached, the non-breaching party may seek various remedies including monetary damages, specific performance, or cancellation and restitution. Expectation damages aim to put the injured party in the position they would have been in had the contract been performed. Consequential damages may be available if they were foreseeable at the time of contract formation.",
                "category": "contract_law",
                "jurisdiction": "common_law"
            },
            {
                "id": "doc11",
                "title": "Unconscionable Contracts",
                "text": "A contract or contract clause may be deemed unconscionable if it is both procedurally and substantively unfair. Procedural unconscionability involves unfair bargaining processes, while substantive unconscionability concerns unfair contract terms. Courts may refuse to enforce unconscionable contracts or specific unconscionable clauses.",
                "category": "contract_law",
                "jurisdiction": "common_law"
            },
            
            # Employment Law
            {
                "id": "doc12",
                "title": "Employment Law - At-Will Employment",
                "text": "At-will employment allows either the employer or employee to terminate the employment relationship at any time, with or without cause, provided the termination does not violate anti-discrimination laws or public policy exceptions. However, there are statutory and common law exceptions that may limit an employer's ability to terminate employees in certain circumstances.",
                "category": "employment_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc13",
                "title": "Title VII - Employment Discrimination",
                "text": "Title VII of the Civil Rights Act of 1964 prohibits employment discrimination based on race, color, religion, sex, or national origin. Employers with 15 or more employees are covered. Discrimination can be shown through disparate treatment (intentional discrimination) or disparate impact (policies that disproportionately affect protected groups).",
                "category": "employment_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc14",
                "title": "Americans with Disabilities Act - Employment",
                "text": "The ADA prohibits employment discrimination against qualified individuals with disabilities. Employers must provide reasonable accommodations that enable disabled employees to perform essential job functions, unless doing so would cause undue hardship. Pre-employment medical examinations are generally prohibited.",
                "category": "employment_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc15",
                "title": "Family and Medical Leave Act",
                "text": "The FMLA provides eligible employees with up to 12 weeks of unpaid, job-protected leave for specified family and medical reasons. Employees must have worked for a covered employer for at least 12 months and 1,250 hours. Leave may be taken for the birth or adoption of a child, serious health conditions, or to care for family members.",
                "category": "employment_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc16",
                "title": "Wage and Hour Laws - FLSA",
                "text": "The Fair Labor Standards Act establishes minimum wage, overtime pay, recordkeeping, and youth employment standards. Non-exempt employees must receive overtime pay at one and one-half times their regular rate for hours worked over 40 in a workweek. Certain employees are exempt from overtime requirements based on salary and job duties.",
                "category": "employment_law",
                "jurisdiction": "federal"
            },
            
            # Constitutional Law
            {
                "id": "doc17",
                "title": "Constitutional Law - Due Process",
                "text": "The Due Process Clause of the Fourteenth Amendment requires that states provide fair procedures before depriving any person of life, liberty, or property. This includes both procedural due process, which focuses on the fairness of procedures, and substantive due process, which protects certain fundamental rights from government interference.",
                "category": "constitutional_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc18",
                "title": "First Amendment - Freedom of Speech",
                "text": "The First Amendment protects freedom of speech from government censorship. Content-based restrictions on speech are subject to strict scrutiny and must serve a compelling government interest through the least restrictive means. Time, place, and manner restrictions on speech in public forums must be content-neutral and narrowly tailored.",
                "category": "constitutional_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc19",
                "title": "Fourth Amendment - Search and Seizure",
                "text": "The Fourth Amendment protects against unreasonable searches and seizures. Generally, police must obtain a warrant based on probable cause before conducting a search. However, there are several exceptions to the warrant requirement, including searches incident to arrest, exigent circumstances, and automobile searches.",
                "category": "constitutional_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc20",
                "title": "Equal Protection Clause",
                "text": "The Equal Protection Clause of the Fourteenth Amendment requires that similarly situated individuals be treated equally under the law. Classifications based on race or national origin are subject to strict scrutiny, gender-based classifications receive intermediate scrutiny, and other classifications are reviewed under rational basis scrutiny.",
                "category": "constitutional_law",
                "jurisdiction": "federal"
            },
            
            # Tort Law
            {
                "id": "doc21",
                "title": "Tort Law - Negligence Standard",
                "text": "To establish negligence, a plaintiff must prove four elements: duty, breach, causation, and damages. The defendant must have owed a duty of care to the plaintiff, breached that duty by failing to meet the standard of reasonable care, and this breach must have been the proximate cause of the plaintiff's damages.",
                "category": "tort_law",
                "jurisdiction": "common_law"
            },
            {
                "id": "doc22",
                "title": "Strict Liability in Tort",
                "text": "Strict liability imposes liability without fault for certain activities deemed inherently dangerous or for defective products. In product liability cases, manufacturers, distributors, and retailers may be held strictly liable for injuries caused by defective products, regardless of negligence. The plaintiff must prove the product was defective and caused injury while being used as intended.",
                "category": "tort_law",
                "jurisdiction": "common_law"
            },
            {
                "id": "doc23",
                "title": "Intentional Torts - Assault and Battery",
                "text": "Assault is the intentional creation of a reasonable apprehension of imminent harmful or offensive contact. Battery is the intentional harmful or offensive contact with another person. Unlike negligence, intentional torts require proof of intent to cause the harm or knowledge that harm is substantially certain to result.",
                "category": "tort_law",
                "jurisdiction": "common_law"
            },
            {
                "id": "doc24",
                "title": "Defamation Law",
                "text": "Defamation involves false statements that harm someone's reputation. Libel refers to written defamation, while slander refers to spoken defamation. Public figures must prove actual malice (knowledge of falsity or reckless disregard for truth) to recover for defamation, while private figures typically need only prove negligence.",
                "category": "tort_law",
                "jurisdiction": "common_law"
            },
            
            # Criminal Law
            {
                "id": "doc25",
                "title": "Criminal Law - Elements of Crime",
                "text": "Most crimes require proof of both actus reus (guilty act) and mens rea (guilty mind). The prosecution must prove each element of the offense beyond a reasonable doubt. Mental states include purposely, knowingly, recklessly, and negligently, with different crimes requiring different levels of mental culpability.",
                "category": "criminal_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc26",
                "title": "Miranda Rights and Custodial Interrogation",
                "text": "Before conducting custodial interrogation, police must inform suspects of their Miranda rights: the right to remain silent, that statements may be used against them, the right to an attorney, and that an attorney will be appointed if they cannot afford one. Failure to give Miranda warnings may result in suppression of statements.",
                "category": "criminal_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc27",
                "title": "Self-Defense Laws",
                "text": "A person may use reasonable force to defend against an imminent threat of unlawful force. The force used must be proportional to the threat faced. Some jurisdictions have 'stand your ground' laws that eliminate the duty to retreat before using force, while others require retreat if it can be done safely.",
                "category": "criminal_law",
                "jurisdiction": "state"
            },
            
            # Family Law
            {
                "id": "doc28",
                "title": "Divorce and Property Division",
                "text": "In divorce proceedings, courts must divide marital property equitably. Community property states divide assets acquired during marriage equally, while equitable distribution states consider factors such as length of marriage, contributions of each spouse, and economic circumstances. Separate property acquired before marriage typically remains with the original owner.",
                "category": "family_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc29",
                "title": "Child Custody and Best Interest Standard",
                "text": "Child custody decisions are based on the best interest of the child standard. Courts consider factors including the child's physical and emotional needs, stability of home environments, relationships with parents, and the child's preferences if age-appropriate. Joint custody is increasingly favored when it serves the child's best interests.",
                "category": "family_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc30",
                "title": "Child Support Guidelines",
                "text": "Child support is typically calculated using state guidelines that consider both parents' incomes, the number of children, and custody arrangements. Support covers basic necessities including housing, food, clothing, and healthcare. Modifications may be granted upon showing a substantial change in circumstances.",
                "category": "family_law",
                "jurisdiction": "state"
            },
            
            # Corporate Law
            {
                "id": "doc31",
                "title": "Corporate Formation and Structure",
                "text": "Corporations are formed by filing articles of incorporation with the state and paying required fees. Corporations provide limited liability protection for shareholders, who are generally not personally liable for corporate debts. Corporate governance involves shareholders, directors, and officers, each with distinct roles and responsibilities.",
                "category": "corporate_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc32",
                "title": "Fiduciary Duties of Directors",
                "text": "Corporate directors owe fiduciary duties of care and loyalty to the corporation and its shareholders. The duty of care requires directors to make informed decisions and exercise reasonable business judgment. The duty of loyalty prohibits self-dealing and requires directors to act in the corporation's best interests.",
                "category": "corporate_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc33",
                "title": "Securities Regulation - Rule 10b-5",
                "text": "Rule 10b-5 under the Securities Exchange Act prohibits fraud in connection with the purchase or sale of securities. Elements include a material misstatement or omission, made with scienter, in connection with a securities transaction, upon which the plaintiff relied and suffered damages. Private parties may bring civil actions under this rule.",
                "category": "corporate_law",
                "jurisdiction": "federal"
            },
            
            # Intellectual Property Law
            {
                "id": "doc34",
                "title": "Patent Law - Patentability Requirements",
                "text": "To be patentable, an invention must be novel, non-obvious, and useful. The invention must also fall within patentable subject matter and not be an abstract idea, law of nature, or natural phenomenon. Patent applications must include a written description that enables a person skilled in the art to make and use the invention.",
                "category": "intellectual_property",
                "jurisdiction": "federal"
            },
            {
                "id": "doc35",
                "title": "Trademark Law - Distinctiveness",
                "text": "Trademarks must be distinctive to receive protection. Inherently distinctive marks include fanciful, arbitrary, and suggestive marks. Descriptive marks can acquire distinctiveness through secondary meaning. Generic terms cannot function as trademarks and receive no protection under trademark law.",
                "category": "intellectual_property",
                "jurisdiction": "federal"
            },
            {
                "id": "doc36",
                "title": "Copyright Law - Fair Use Doctrine",
                "text": "Fair use allows limited use of copyrighted material without permission for purposes such as criticism, comment, news reporting, teaching, or research. Courts consider four factors: purpose and character of use, nature of copyrighted work, amount used, and effect on the market for the original work.",
                "category": "intellectual_property",
                "jurisdiction": "federal"
            },
            
            # Immigration Law
            {
                "id": "doc37",
                "title": "Immigration Law - Asylum Requirements",
                "text": "To qualify for asylum, an applicant must demonstrate persecution or well-founded fear of persecution based on race, religion, nationality, political opinion, or membership in a particular social group. The persecution must be by the government or groups the government cannot or will not control. Applications must generally be filed within one year of arrival.",
                "category": "immigration_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc38",
                "title": "Naturalization Process",
                "text": "To become a U.S. citizen through naturalization, permanent residents must meet residence and physical presence requirements, demonstrate English proficiency and civics knowledge, and show good moral character. The process includes filing Form N-400, attending a biometrics appointment, and passing an interview and examination.",
                "category": "immigration_law",
                "jurisdiction": "federal"
            },
            
            # Environmental Law
            {
                "id": "doc39",
                "title": "Clean Air Act - National Ambient Air Quality Standards",
                "text": "The Clean Air Act requires EPA to establish National Ambient Air Quality Standards (NAAQS) for criteria pollutants harmful to public health and welfare. States must develop implementation plans to achieve and maintain these standards. The Act also regulates emissions from stationary and mobile sources.",
                "category": "environmental_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc40",
                "title": "CERCLA Superfund Liability",
                "text": "The Comprehensive Environmental Response, Compensation, and Liability Act (CERCLA) imposes strict, joint, and several liability on potentially responsible parties for cleanup of contaminated sites. Liable parties include current and former owners/operators, generators, and transporters of hazardous substances.",
                "category": "environmental_law",
                "jurisdiction": "federal"
            },
            
            # Tax Law
            {
                "id": "doc41",
                "title": "Federal Income Tax - Business Deductions",
                "text": "Business expenses are deductible if they are ordinary and necessary for carrying on a trade or business. Ordinary expenses are common and accepted in the taxpayer's business, while necessary expenses are helpful and appropriate. Personal expenses are generally not deductible, but some mixed-use expenses may be partially deductible.",
                "category": "tax_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc42",
                "title": "Estate Tax and Gift Tax",
                "text": "The federal estate tax applies to transfers of property at death, while the gift tax applies to lifetime transfers. Both taxes share a unified credit that allows tax-free transfers up to a certain amount. Annual gift tax exclusions permit tax-free gifts up to specified amounts per recipient per year.",
                "category": "tax_law",
                "jurisdiction": "federal"
            },
            
            # Healthcare Law
            {
                "id": "doc43",
                "title": "HIPAA Privacy Rule",
                "text": "The HIPAA Privacy Rule protects individually identifiable health information held by covered entities. Patients have rights to access their health information, request corrections, and receive notice of privacy practices. Covered entities must implement safeguards to protect health information and limit uses and disclosures.",
                "category": "healthcare_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc44",
                "title": "Medical Malpractice Standards",
                "text": "Medical malpractice occurs when a healthcare provider deviates from the standard of care and causes injury to a patient. The standard of care is what a reasonably competent provider in the same specialty would do under similar circumstances. Expert testimony is typically required to establish the standard of care and breach.",
                "category": "healthcare_law",
                "jurisdiction": "state"
            },
            
            # Banking and Finance Law
            {
                "id": "doc45",
                "title": "Truth in Lending Act",
                "text": "The Truth in Lending Act (TILA) requires lenders to disclose credit terms and costs to consumers. Key disclosures include the annual percentage rate (APR), finance charges, and total payments. TILA also provides consumers with the right to rescind certain credit transactions within three business days.",
                "category": "banking_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc46",
                "title": "Fair Credit Reporting Act",
                "text": "The Fair Credit Reporting Act regulates the collection and use of consumer credit information. Consumers have the right to obtain free credit reports annually, dispute inaccurate information, and receive notice when adverse actions are taken based on credit reports. Credit reporting agencies must follow reasonable procedures to ensure accuracy.",
                "category": "banking_law",
                "jurisdiction": "federal"
            },
            
            # Insurance Law
            {
                "id": "doc47",
                "title": "Insurance Policy Interpretation",
                "text": "Insurance policies are contracts that are interpreted according to contract law principles. Ambiguous terms are construed against the insurer and in favor of coverage. The reasonable expectations of the insured are considered, and policies are read as a whole to determine coverage. Exclusions are strictly construed.",
                "category": "insurance_law",
                "jurisdiction": "state"
            },
            {
                "id": "doc48",
                "title": "Bad Faith Insurance Claims",
                "text": "Insurers have an implied duty of good faith and fair dealing toward their insureds. Bad faith occurs when an insurer unreasonably denies or delays payment of a valid claim. Remedies for bad faith may include compensatory damages, consequential damages, and in some jurisdictions, punitive damages.",
                "category": "insurance_law",
                "jurisdiction": "state"
            },
            
            # Administrative Law
            {
                "id": "doc49",
                "title": "Administrative Procedure Act",
                "text": "The Administrative Procedure Act (APA) governs federal agency rulemaking and adjudication. The APA requires agencies to follow specific procedures for notice-and-comment rulemaking and provides standards for judicial review of agency actions. Courts review agency interpretations of law de novo but defer to reasonable agency interpretations under Chevron doctrine.",
                "category": "administrative_law",
                "jurisdiction": "federal"
            },
            {
                "id": "doc50",
                "title": "Freedom of Information Act",
                "text": "The Freedom of Information Act (FOIA) provides the public with access to federal agency records. Agencies must respond to FOIA requests within specified timeframes and may charge fees for processing. Nine exemptions protect certain types of information from disclosure, including classified information, trade secrets, and law enforcement records.",
                "category": "administrative_law",
                "jurisdiction": "federal"
            }
        ]
        
        # Connect to MongoDB
        mongo_uri = os.getenv("MONGO_DB_URI")
        if not mongo_uri:
            logger.error("MONGO_DB_URI environment variable not set")
            raise ValueError("MONGO_DB_URI environment variable must be set in .env file")
        
        logger.info(f"Connecting to MongoDB...")
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=5000,
            tlsAllowInvalidCertificates=True  # For development with MongoDB Atlas
        )
        
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        db = client["legal_rag"]
        collection = db["docs"]
        
        # Create index for efficient searching
        collection.create_index("id", unique=True)
        collection.create_index("category")
        collection.create_index("jurisdiction")
        logger.info("Database indexes created")
        
        # Check if documents already exist
        existing_count = collection.count_documents({})
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing documents. Clearing collection...")
            collection.delete_many({})
        
        # Generate embeddings and store documents
        logger.info("Generating embeddings and storing documents...")
        
        # Extract text for embedding generation
        texts = [doc["text"] for doc in legal_docs]
        embeddings, vectorizer = get_embeddings(texts)
        
        if embeddings is None:
            logger.error("Failed to generate embeddings")
            return False
        
        # Store documents with embeddings
        for i, doc in enumerate(legal_docs):
            try:
                # Add embedding to document
                doc["embedding"] = embeddings[i].tolist()
                
                # Insert document
                result = collection.insert_one(doc.copy())
                logger.info(f"Stored document {i+1}/{len(legal_docs)}: {doc['title']}")
                
            except Exception as e:
                logger.error(f"Error processing document {doc['id']}: {str(e)}")
                continue
        
        # Store the vectorizer parameters for later use
        # Convert numpy types to Python types for MongoDB compatibility
        vocabulary = {word: int(idx) for word, idx in vectorizer.vocabulary_.items()}
        
        vectorizer_params = {
            "vocabulary": vocabulary,
            "idf": vectorizer.idf_.tolist() if hasattr(vectorizer, 'idf_') else None,
            "max_features": vectorizer.max_features,
            "stop_words": list(vectorizer.stop_words_) if hasattr(vectorizer, 'stop_words_') and vectorizer.stop_words_ is not None else None
        }
        
        # Store vectorizer info in a separate collection
        vectorizer_collection = db["vectorizer"]
        vectorizer_collection.delete_many({})  # Clear existing
        vectorizer_collection.insert_one({"type": "tfidf", "params": vectorizer_params})
        
        # Verify the setup
        final_count = collection.count_documents({})
        logger.info(f"Database setup complete! Stored {final_count} documents")
        
        # Test a sample query
        logger.info("Testing document retrieval...")
        sample_doc = collection.find_one({"id": "doc2"})
        if sample_doc:
            logger.info(f"Sample document retrieved: {sample_doc['title']}")
        
        logger.info("✅ Legal document database setup completed successfully!")
        return True
        
    except ConnectionFailure:
        logger.error("❌ Failed to connect to MongoDB. Please check your connection string and network.")
        return False
    except ServerSelectionTimeoutError:
        logger.error("❌ MongoDB server selection timeout. Please verify the server is running.")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during setup: {str(e)}")
        return False
    finally:
        try:
            client.close()
            logger.info("MongoDB connection closed")
        except:
            pass

if __name__ == "__main__":
    setup_legal_document_database()
