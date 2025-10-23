from uagents import Agent, Context, Model
import os
from config.agent_addresses import SCORER_ADDRESS

# Data Models
class EnrichedSkillsProfile(Model):
    candidate_id: str
    original_skills: list
    related_skills: list
    skill_categories: dict
    market_demand: dict
    experience_years: int
    preferences: dict

class JobListing(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    requirements: list
    description: str
    salary_range: str
    location: str
    remote: bool

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 4
# SCORER_ADDRESS = os.environ.get("SCORER_ADDRESS")

# Initialize Agent
job_discovery_agent = Agent(
    name="Job Discovery Agent",
    port=8003,
    seed="job_discovery_seed_789",
    endpoint=["http://localhost:8003/submit"]
)

# Job Database (Mock - In production use LangChain + FAISS)
JOB_DATABASE = [
    {
        "job_id": "JOB001",
        "title": "Senior Python Developer",
        "company": "TechCorp AI",
        "requirements": ["python", "django", "aws", "sql", "docker"],
        "description": "Build scalable backend systems for AI applications",
        "salary_range": "$120k-$160k",
        "location": "San Francisco, CA",
        "remote": True
    },
    {
        "job_id": "JOB002",
        "title": "Machine Learning Engineer",
        "company": "DataScience Pro",
        "requirements": ["python", "machine learning", "tensorflow", "aws"],
        "description": "Develop ML models for predictive analytics",
        "salary_range": "$140k-$180k",
        "location": "New York, NY",
        "remote": True
    },
    {
        "job_id": "JOB003",
        "title": "Full Stack Developer",
        "company": "WebSolutions Inc",
        "requirements": ["javascript", "react", "node.js", "mongodb"],
        "description": "Build modern web applications",
        "salary_range": "$110k-$150k",
        "location": "Austin, TX",
        "remote": True
    },
    {
        "job_id": "JOB004",
        "title": "DevOps Engineer",
        "company": "CloudFirst",
        "requirements": ["aws", "kubernetes", "docker", "ci/cd"],
        "description": "Manage cloud infrastructure",
        "salary_range": "$130k-$170k",
        "location": "Seattle, WA",
        "remote": True
    },
    {
        "job_id": "JOB005",
        "title": "Engineering Manager",
        "company": "InnovateTech",
        "requirements": ["leadership", "python", "agile"],
        "description": "Lead engineering team",
        "salary_range": "$150k-$200k",
        "location": "Boston, MA",
        "remote": False
    }
]

def semantic_job_search(profile: EnrichedSkillsProfile) -> list:
    all_skills = set(
        skill.lower() for skill in 
        profile.original_skills + profile.related_skills
    )
    
    matched_jobs = []
    
    for job in JOB_DATABASE:
        job_requirements = set(req.lower() for req in job["requirements"])
        matching_skills = all_skills.intersection(job_requirements)
        
        if matching_skills:
            match_percentage = (len(matching_skills) / len(job_requirements)) * 100
            matched_jobs.append({
                **job,
                "matching_skills": list(matching_skills),
                "match_percentage": match_percentage
            })
    
    matched_jobs.sort(key=lambda x: x["match_percentage"], reverse=True)
    return matched_jobs[:5]

@job_discovery_agent.on_message(model=EnrichedSkillsProfile)
async def discover_jobs(ctx: Context, sender: str, msg: EnrichedSkillsProfile):
    ctx.logger.info(f"📥 Enriched profile received: {msg.candidate_id}")
    ctx.logger.info(f"🔍 Searching jobs...")
    
    matching_jobs = semantic_job_search(msg)
    
    ctx.logger.info(f"✅ Found {len(matching_jobs)} matching jobs")
    
    for job_data in matching_jobs:
        job_listing = JobListing(
            job_id=job_data["job_id"],
            candidate_id=msg.candidate_id,
            title=job_data["title"],
            company=job_data["company"],
            requirements=job_data["requirements"],
            description=job_data["description"],
            salary_range=job_data["salary_range"],
            location=job_data["location"],
            remote=job_data["remote"]
        )
        
        if "PUT_AGENT" not in SCORER_ADDRESS:
            await ctx.send(SCORER_ADDRESS, job_listing)
            ctx.logger.info(f"📤 Sent {job_data['title']} to Scorer")
        else:
            ctx.logger.error("❌ SCORER_ADDRESS not configured!")

@job_discovery_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 JOB DISCOVERY AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8003")

if __name__ == "__main__":
    job_discovery_agent.run()