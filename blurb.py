from typing import List, Dict, Any


def _generate_questions_from_raw_texts() -> List[Dict[str, Any]]:
    questions_data = [
        {
            "id": 0,
            "source_blurb_topic": "Password Standards",
            "question": "According to NIST SP 800-63B, what is the minimum password length when a password is the only authenticator?",
            "options": ["A) 8 characters", "B) 10 characters", "C) 15 characters"],
            "answer_index": 2
        },
        {
            "id": 1,
            "source_blurb_topic": "Password Policy",
            "question": "Which password policy is discouraged by NIST?",
            "options": ["A) Enforcing character composition rules", "B) Screening against breached password lists", "C) Supporting long passphrases"],
            "answer_index": 0
        },
        {
            "id": 2,
            "source_blurb_topic": "MFA",
            "question": "Which MFA method is considered phishing-resistant by NIST?",
            "options": ["A) SMS codes", "B) FIDO2/WebAuthn keys", "C) Security questions"],
            "answer_index": 1
        },
        {
            "id": 3,
            "source_blurb_topic": "Password Expiration",
            "question": "When should users change their passwords according to NIST?",
            "options": ["A) Every 30 days", "B) Only if there is evidence of compromise", "C) Every login"],
            "answer_index": 1
        },
        {
            "id": 4,
            "source_blurb_topic": "Public Wi-Fi",
            "question": "What is the recommended precaution when using public Wi-Fi?",
            "options": ["A) Disable firewalls", "B) Use a VPN", "C) Trust HTTPS automatically"],
            "answer_index": 1
        },
        {
            "id": 5,
            "source_blurb_topic": "Encryption",
            "question": "What does full-disk encryption mainly protect?",
            "options": ["A) Data on a stolen powered-off device", "B) Malware infections", "C) Phishing attacks"],
            "answer_index": 0
        },
        {
            "id": 6,
            "source_blurb_topic": "Updates",
            "question": "Why does CISA stress timely updates?",
            "options": ["A) Improve battery life", "B) Patch active vulnerabilities", "C) Add interface features"],
            "answer_index": 1
        },
        {
            "id": 7,
            "source_blurb_topic": "Account Security",
            "question": "Why is password reuse unsafe?",
            "options": ["A) Easier memory", "B) Breach of one account compromises others", "C) Faster login"],
            "answer_index": 1
        },
        {
            "id": 8,
            "source_blurb_topic": "MFA",
            "question": "Which combination is strong MFA?",
            "options": ["A) Password + security questions", "B) Password + authenticator app", "C) Password + favorite color"],
            "answer_index": 1
        },
        {
            "id": 9,
            "source_blurb_topic": "Incident Response",
            "question": "What is the FIRST step after detecting suspicious activity?",
            "options": ["A) Delete the account", "B) Contain and analyze the event", "C) Notify all users immediately"],
            "answer_index": 1
        },
        {
            "id": 10,
            "source_blurb_topic": "Phishing",
            "question": "Which is the safest action if you suspect a phishing email?",
            "options": ["A) Click the link to verify", "B) Report and delete it", "C) Reply asking for confirmation"],
            "answer_index": 1
        },
        {
            "id": 11,
            "source_blurb_topic": "Backups",
            "question": "What is the most secure backup practice?",
            "options": ["A) Store backups online only", "B) Use offline backups", "C) Rely on auto-save"],
            "answer_index": 1
        },
        {
            "id": 12,
            "source_blurb_topic": "Device Security",
            "question": "What is the benefit of automatic screen lock?",
            "options": ["A) Saves battery", "B) Prevents unauthorized access", "C) Speeds up booting"],
            "answer_index": 1
        },
        {
            "id": 13,
            "source_blurb_topic": "Access Control",
            "question": "What does the principle of least privilege mean?",
            "options": ["A) Users get maximum permissions", "B) Users get only what they need", "C) Users get no permissions"],
            "answer_index": 1
        },
        {
            "id": 14,
            "source_blurb_topic": "VPN",
            "question": "What is the main purpose of a VPN?",
            "options": ["A) Encrypt traffic", "B) Speed up internet", "C) Block pop-ups"],
            "answer_index": 0
        },
        {
            "id": 15,
            "source_blurb_topic": "Data Protection",
            "question": "Which is considered sensitive personally identifiable information (PII)?",
            "options": ["A) Favorite food", "B) Social Security Number", "C) Shoe size"],
            "answer_index": 1
        },
        {
            "id": 16,
            "source_blurb_topic": "Malware",
            "question": "What is ransomware?",
            "options": ["A) Malware that locks data until payment", "B) Malware that sends spam", "C) Malware that tracks keystrokes"],
            "answer_index": 0
        },
        {
            "id": 17,
            "source_blurb_topic": "Updates",
            "question": "Which update type is most critical for security?",
            "options": ["A) Security patches", "B) Interface changes", "C) Battery optimizations"],
            "answer_index": 0
        },
        {
            "id": 18,
            "source_blurb_topic": "Firewalls",
            "question": "What is the main purpose of a firewall?",
            "options": ["A) Block unauthorized access", "B) Increase Wi-Fi speed", "C) Store backups"],
            "answer_index": 0
        },
        {
            "id": 19,
            "source_blurb_topic": "Social Engineering",
            "question": "What is tailgating in cybersecurity?",
            "options": ["A) Malware infection", "B) Following someone into a secure area", "C) Reusing passwords"],
            "answer_index": 1
        },
        {
            "id": 20,
            "source_blurb_topic": "Incident Response",
            "question": "Which comes first in the NIST Incident Response lifecycle?",
            "options": ["A) Detection and analysis", "B) Containment", "C) Preparation"],
            "answer_index": 2
        },
        {
            "id": 21,
            "source_blurb_topic": "Password Storage",
            "question": "How should passwords be stored?",
            "options": ["A) In plaintext", "B) Hashed with salt", "C) In a text file"],
            "answer_index": 1
        },
        {
            "id": 22,
            "source_blurb_topic": "IoT Security",
            "question": "What is a key risk of IoT devices?",
            "options": ["A) Immune to attacks", "B) Often lack strong security", "C) Cannot connect online"],
            "answer_index": 1
        },
        {
            "id": 23,
            "source_blurb_topic": "Cloud Security",
            "question": "Who shares responsibility for cloud security?",
            "options": ["A) Cloud provider only", "B) User and provider", "C) User only"],
            "answer_index": 1
        },
        {
            "id": 24,
            "source_blurb_topic": "MFA",
            "question": "What is an example of 'something you are'?",
            "options": ["A) Password", "B) Fingerprint", "C) Security token"],
            "answer_index": 1
        },
        {
            "id": 25,
            "source_blurb_topic": "Email Security",
            "question": "Which attachment type is most risky?",
            "options": ["A) .exe", "B) .txt", "C) .jpg"],
            "answer_index": 0
        },
        {
            "id": 26,
            "source_blurb_topic": "Patch Management",
            "question": "What is patch management?",
            "options": ["A) Fixing software vulnerabilities", "B) Changing user passwords", "C) Replacing hardware"],
            "answer_index": 0
        },
        {
            "id": 27,
            "source_blurb_topic": "DDoS",
            "question": "What is the goal of a DDoS attack?",
            "options": ["A) Encrypt data", "B) Overwhelm services", "C) Steal login credentials"],
            "answer_index": 1
        },
        {
            "id": 28,
            "source_blurb_topic": "Wireless Security",
            "question": "Which Wi-Fi encryption is strongest?",
            "options": ["A) WEP", "B) WPA2/WPA3", "C) Open network"],
            "answer_index": 1
        },
        {
            "id": 29,
            "source_blurb_topic": "Security Awareness",
            "question": "Why is user training critical?",
            "options": ["A) Users detect phishing", "B) Users configure firewalls", "C) Users create patches"],
            "answer_index": 0
        },
        {
            "id": 30,
            "source_blurb_topic": "Logs",
            "question": "Why are security logs important?",
            "options": ["A) Entertainment", "B) Detecting suspicious activity", "C) Faster boot time"],
            "answer_index": 1
        },
        {
            "id": 31,
            "source_blurb_topic": "Physical Security",
            "question": "Which is a good physical security control?",
            "options": ["A) Strong passwords", "B) Biometric locks", "C) Firewalls"],
            "answer_index": 1
        },
        {
            "id": 32,
            "source_blurb_topic": "Data Security",
            "question": "Which is an example of data in transit?",
            "options": ["A) Email being sent", "B) File on a hard drive", "C) Printed document"],
            "answer_index": 0
        },
        {
            "id": 33,
            "source_blurb_topic": "Cyber Hygiene",
            "question": "Which is part of good cyber hygiene?",
            "options": ["A) Reusing passwords", "B) Regular software updates", "C) Ignoring patches"],
            "answer_index": 1
        },
        {
            "id": 34,
            "source_blurb_topic": "Encryption",
            "question": "What is asymmetric encryption?",
            "options": ["A) Same key for encrypt/decrypt", "B) Different keys for encrypt/decrypt", "C) No keys used"],
            "answer_index": 1
        },
        {
            "id": 35,
            "source_blurb_topic": "Mobile Security",
            "question": "Which practice secures mobile devices?",
            "options": ["A) Disable updates", "B) Use device encryption", "C) Use default PIN"],
            "answer_index": 1
        },
        {
            "id": 36,
            "source_blurb_topic": "Threats",
            "question": "What is a zero-day vulnerability?",
            "options": ["A) Unknown and unpatched flaw", "B) Malware detected immediately", "C) Firewall misconfiguration"],
            "answer_index": 0
        },
        {
            "id": 37,
            "source_blurb_topic": "Certificates",
            "question": "What does HTTPS use to secure traffic?",
            "options": ["A) Digital certificates", "B) Firewalls", "C) Security questions"],
            "answer_index": 0
        },
        {
            "id": 38,
            "source_blurb_topic": "Access Control",
            "question": "What is role-based access control (RBAC)?",
            "options": ["A) Access based on job role", "B) Access for everyone", "C) Random access"],
            "answer_index": 0
        },
        {
            "id": 39,
            "source_blurb_topic": "Network Security",
            "question": "What is network segmentation?",
            "options": ["A) Splitting networks for security", "B) Combining all networks", "C) Removing all firewalls"],
            "answer_index": 0
        },
        {
            "id": 40,
            "source_blurb_topic": "MFA",
            "question": "What is an example of 'something you have'?",
            "options": ["A) Password", "B) Security token", "C) Fingerprint"],
            "answer_index": 1
        },
        {
            "id": 41,
            "source_blurb_topic": "Risk Management",
            "question": "Which is part of risk management?",
            "options": ["A) Accept, mitigate, or transfer risks", "B) Ignore all risks", "C) Eliminate all risks always"],
            "answer_index": 0
        },
        {
            "id": 42,
            "source_blurb_topic": "Data Protection",
            "question": "What is data minimization?",
            "options": ["A) Collect only necessary data", "B) Collect all possible data", "C) Delete all data"],
            "answer_index": 0
        },
        {
            "id": 43,
            "source_blurb_topic": "Malware",
            "question": "What is spyware?",
            "options": ["A) Software that monitors secretly", "B) Software that encrypts data", "C) Software that blocks firewalls"],
            "answer_index": 0
        },
        {
            "id": 44,
            "source_blurb_topic": "Authentication",
            "question": "What is single sign-on (SSO)?",
            "options": ["A) One login gives access to many systems", "B) One password per account", "C) One-time password only"],
            "answer_index": 0
        },
        {
            "id": 45,
            "source_blurb_topic": "Cloud",
            "question": "What is a key benefit of cloud backups?",
            "options": ["A) Offsite storage resilience", "B) Faster local recovery", "C) No internet needed"],
            "answer_index": 0
        },
        {
            "id": 46,
            "source_blurb_topic": "Monitoring",
            "question": "What is continuous monitoring?",
            "options": ["A) Ongoing detection of threats", "B) Check logs once a year", "C) Disable alerts"],
            "answer_index": 0
        },
        {
            "id": 47,
            "source_blurb_topic": "Vulnerability Management",
            "question": "What is the first step in vulnerability management?",
            "options": ["A) Scanning systems", "B) Applying patches", "C) Writing policies"],
            "answer_index": 0
        },
        {
            "id": 48,
            "source_blurb_topic": "Security Testing",
            "question": "What is penetration testing?",
            "options": ["A) Simulated attack to find weaknesses", "B) Installing antivirus", "C) Changing passwords"],
            "answer_index": 0
        },
        {
            "id": 49,
            "source_blurb_topic": "Privacy",
            "question": "What is the main goal of GDPR?",
            "options": ["A) Protect personal data privacy", "B) Increase internet speed", "C) Enforce software updates"],
            "answer_index": 0
        },
        {
            "id": 50,
            "source_blurb_topic": "Threat Intelligence",
            "question": "What is threat intelligence used for?",
            "options": ["A) Understanding attacker tactics", "B) Designing websites", "C) Improving Wi-Fi"],
            "answer_index": 0
        },
        {
            "id": 51,
            "source_blurb_topic": "Cybersecurity Framework",
            "question": "Which are NIST CSF core functions?",
            "options": ["A) Identify, Protect, Detect, Respond, Recover", "B) Write, Read, Edit, Delete", "C) Send, Receive, Store"],
            "answer_index": 0
        },
    ]
    return questions_data


ALL_QUESTIONS_DATA = _generate_questions_from_raw_texts()
