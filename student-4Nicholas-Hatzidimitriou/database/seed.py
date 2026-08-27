import sqlite3
import os
from pathlib import Path

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
DB_FILE = Path(DATA_DIR) / "student4.db"

conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

research_projects = [
    (1, "AI-Driven Curriculum Analytics", "Using AI to analyse curriculum effectiveness across faculties", "Computer Science", "in progress", "2025-02-01", "2026-06-30", 1),
    (2, "Sustainable Campus Energy Systems", "Research into renewable energy integration on campus", "Engineering", "in progress", "2024-09-01", "2026-03-31", 2),
    (3, "Student Mental Health Trends", "Longitudinal study of student wellbeing post-pandemic", "Psychology", "completed", "2023-01-01", "2025-01-31", 3),
    (4, "Blockchain for Academic Credentials", "Exploring blockchain-based degree verification systems", "Computer Science", "proposed", "2026-01-01", "2027-12-31", 4),
    (5, "Climate Impact on Regional Agriculture", "Assessing climate change effects on local farming", "Environmental Science", "in progress", "2024-06-01", "2026-05-31", 5),
    (6, "Machine Learning in Medical Diagnostics", "Applying ML models to early disease detection", "Health Sciences", "in progress", "2025-01-15", "2026-12-31", 6),
    (7, "Urban Transport Optimisation", "Modelling public transport efficiency in metro areas", "Engineering", "on hold", "2023-08-01", "2025-08-01", 2),
    (8, "Digital Literacy in Aging Populations", "Studying technology adoption among older adults", "Sociology", "proposed", "2026-03-01", "2027-06-30", 7),
    (9, "Financial Risk Modelling with AI", "AI-based approaches to predicting financial market risk", "Finance", "completed", "2023-05-01", "2024-11-30", 8),
    (10, "Renewable Water Purification Methods", "Investigating low-cost water purification for rural areas", "Environmental Science", "in progress", "2025-04-01", "2026-10-31", 5),
]
cursor.executemany(
    """INSERT INTO ResearchProjects
       (projectID, title, description, department, status, startDate, endDate, leadStaffID)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    research_projects
)

grants = [
    (1, 1, "Australian Research Council", 150000.00, 140000.00, "2025-01-15", "awarded"),
    (2, 2, "CSIRO Energy Fund", 220000.00, None, "2024-08-01", "applied"),
    (3, 3, "National Health & Medical Research Council", 95000.00, 95000.00, "2022-11-01", "completed"),
    (4, 4, "Digital Innovation Grant Scheme", 60000.00, None, "2025-12-01", "applied"),
    (5, 5, "Environmental Sustainability Trust", 180000.00, 175000.00, "2024-05-01", "awarded"),
    (6, 6, "Medical Research Future Fund", 300000.00, None, "2025-01-10", "in progress"),
    (7, 7, "State Transport Innovation Grant", 75000.00, 0.00, "2023-07-01", "rejected"),
    (8, 8, "Social Sciences Research Fund", 40000.00, None, "2026-02-15", "applied"),
    (9, 9, "Fintech Research Partnership", 110000.00, 110000.00, "2023-04-01", "completed"),
    (10, 10, "Global Water Innovation Fund", 130000.00, 120000.00, "2025-03-01", "awarded"),
]
cursor.executemany(
    """INSERT INTO Grants
       (grantID, projectID, fundingBody, amountRequested, amountAwarded, applicationDeadline, status)
       VALUES (?, ?, ?, ?, ?, ?, ?)""",
    grants
)

publications = [
    (1, 1, 1, "Analysing Curriculum Effectiveness with Machine Learning", "journal", "Journal of Educational Technology", "2025-11-10"),
    (2, 2, 2, "Integrating Solar Microgrids into University Campuses", "conference", "IEEE Energy Systems Conference", "2025-06-20"),
    (3, 3, 3, "Post-Pandemic Mental Health Trajectories in Students", "journal", "Journal of Student Wellbeing", "2025-02-05"),
    (4, 5, 5, "Modelling Climate Risk for Regional Crop Yields", "journal", "Environmental Research Letters", "2025-09-15"),
    (5, 6, 6, "Early Detection of Diabetic Retinopathy using CNNs", "conference", "International Conference on Medical AI", "2025-10-01"),
    (6, 9, 8, "Predicting Market Volatility with Deep Learning", "journal", "Journal of Financial Engineering", "2024-09-12"),
    (7, 3, 3, "Digital Wellbeing Interventions for University Students", "report", "Internal University Report", "2024-12-01"),
    (8, 5, 5, "Low-Cost Water Purification for Developing Regions", "conference", "World Water Innovation Summit", "2026-01-18"),
    (9, 1, 4, "Blockchain Feasibility for Credential Verification", "book chapter", "Advances in Educational Technology (Springer)", "2026-02-01"),
    (10, 9, 8, "Risk-Adjusted Portfolio Optimisation using AI", "journal", "Quantitative Finance Review", "2024-06-22"),
]
cursor.executemany(
    """INSERT INTO Publications
       (publicationID, projectID, staffID, title, publicationType, journalOrVenue, datePublished)
       VALUES (?, ?, ?, ?, ?, ?, ?)""",
    publications
)

project_staff = [
    (1, 1, 1, "lead"),
    (2, 1, 4, "co-investigator"),
    (3, 2, 2, "lead"),
    (4, 2, 7, "research assistant"),
    (5, 3, 3, "lead"),
    (6, 5, 5, "lead"),
    (7, 5, 6, "co-investigator"),
    (8, 6, 6, "lead"),
    (9, 8, 7, "lead"),
    (10, 9, 8, "lead"),
]
cursor.executemany(
    """INSERT INTO ProjectStaff
       (projectStaffID, projectID, staffID, role)
       VALUES (?, ?, ?, ?)""",
    project_staff
)

grant_alerts = [
    (1, 1, "status change", "2025-01-16", "resolved"),
    (2, 2, "deadline approaching", "2024-07-25", "resolved"),
    (3, 3, "status change", "2022-11-05", "resolved"),
    (4, 4, "missing documents", "2025-11-20", "active"),
    (5, 4, "deadline approaching", "2025-11-28", "active"),
    (6, 5, "status change", "2024-05-03", "resolved"),
    (7, 6, "deadline approaching", "2025-01-05", "dismissed"),
    (8, 7, "status change", "2023-07-10", "resolved"),
    (9, 8, "missing documents", "2026-02-10", "active"),
    (10, 10, "status change", "2025-03-04", "resolved"),
]
cursor.executemany(
    """INSERT INTO GrantAlerts
       (alertID, grantID, alertType, dueDate, status)
       VALUES (?, ?, ?, ?, ?)""",
    grant_alerts
)

research_ai_analysis = [
    (1, 1, None, "Project shows strong alignment with AI-in-education research trends and has produced one peer-reviewed publication.", "[1,4]", "Staff 1 has expertise in AI/EdTech; Staff 4 has blockchain expertise relevant to future project phases.", "2026-01-05 09:12:00"),
    (2, None, 5, "Staff member has authored 2 publications and leads 2 active projects, showing high research productivity in sustainability.", "[5,6]", "Cross-project synergy identified between environmental and health-diagnostics research staff.", "2026-01-06 10:00:00"),
    (3, 2, None, "Renewable energy project has strong industry partnership potential but is not yet fully funded.", "[2,7]", "Staff 2 leads the project; Staff 7 has complementary transport-systems expertise.", "2026-01-07 14:30:00"),
    (4, None, 8, "Staff member shows consistent output in financial AI research with 2 completed grants.", "[8]", "Self-match: staff already positioned as domain expert for future fintech grants.", "2026-01-08 11:45:00"),
    (5, 6, None, "Medical diagnostics project is well-funded and progressing on schedule.", "[6,3]", "Staff 3 (psychology/wellbeing) could contribute a patient-experience research angle.", "2026-01-09 08:20:00"),
    (6, None, 3, "Staff member has completed a major NHMRC-funded project and has capacity for new research.", "[3]", "High availability and strong track record in mental health research.", "2026-01-10 13:15:00"),
    (7, 9, None, "Fintech project successfully completed with two related publications produced.", "[8]", "Staff 8 led the project and is best positioned for follow-up research.", "2026-01-11 09:50:00"),
    (8, None, 7, "Staff member is under-allocated to research projects relative to workload capacity.", "[8,2]", "Recommend collaboration on transport-innovation or fintech-adjacent digital literacy studies.", "2026-01-12 15:05:00"),
    (9, 5, None, "Water purification project has awarded funding and strong potential for publication output.", "[5]", "Staff 5 already leading; recommend increasing research assistant support.", "2026-01-13 10:40:00"),
    (10, None, 4, "Staff member has one proposed project pending approval, indicating early-stage research pipeline.", "[4,1]", "Recommend pairing with Staff 1 given overlapping interest in EdTech/blockchain integration.", "2026-01-14 16:22:00"),
]
cursor.executemany(
    """INSERT INTO ResearchAIAnalysis
       (analysisID, projectID, staffID, generatedSummary, recommendedStaffMatches, matchRationale, dateGenerated)
       VALUES (?, ?, ?, ?, ?, ?, ?)""",
    research_ai_analysis
)

conn.commit()
conn.close()

print("Seed data inserted successfully.")