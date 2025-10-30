from uagents import Model

class CandidateProfile(Model):
    """Profile extracted from resume - sent from Candidate to Job Discovery"""
    candidate_id: str
    resume_text: str
    skills: list
    experience_years: int
    preferences: dict

class JobListing(Model):
    """Individual job - sent from Job Discovery to Recommendation"""
    job_id: str
    candidate_id: str
    title: str
    company: str
    description: str
    requirements: list
    salary_range: str
    location: str
    remote: bool
    source_url: str
    match_score: float  # Pre-calculated by discovery agent

class RecommendationReport(Model):
    """Final report - sent from Recommendation back to Candidate"""
    candidate_id: str
    report: str
    top_matches: list

class JobListingBatch(Model):
    """Batch of job listings - sent from Job Discovery to Recommendation"""
    candidate_id: str
    jobs: list  # List of job dictionaries
    total_count: int

class ErrorReport(Model):
    candidate_id: str
    content : str

class PDFResume(Model):
    """PDF resume upload"""
    content: str  # base64 encoded

