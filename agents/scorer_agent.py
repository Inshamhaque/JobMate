from uagents import Agent, Context, Model
import os
from config.agent_addresses import RECOMMENDER_ADDRESS
# Data Models
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

class MatchScore(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    match_score: float
    reasoning: str
    skill_gaps: list
    strengths: list
    salary_range: str
    location: str
    remote: bool

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 5
# RECOMMENDER_ADDRESS = os.environ.get("RECOMMENDER_ADDRESS")

# Initialize Agent
scorer_agent = Agent(
    name="Compatibility Scorer Agent",
    port=8004,
    seed="scorer_seed_abc",
    endpoint=["http://localhost:8004/submit"]
)

def calculate_compatibility_score(job: JobListing) -> dict:
    # Mock candidate skills (in production, retrieve from context)
    candidate_skills = ["python", "django", "aws", "docker", "machine learning"]
    
    matching_skills = [
        skill for skill in job.requirements 
        if skill.lower() in [s.lower() for s in candidate_skills]
    ]
    missing_skills = [
        skill for skill in job.requirements 
        if skill.lower() not in [s.lower() for s in candidate_skills]
    ]
    
    base_score = 75.0
    if len(job.requirements) > 0:
        base_score = (len(matching_skills) / len(job.requirements)) * 100
    
    if job.remote:
        base_score += 5
    
    reasoning = f'''
Match Analysis for {job.title} at {job.company}:

✅ Matching Skills ({len(matching_skills)}/{len(job.requirements)}):
{', '.join(matching_skills) if matching_skills else 'None'}

⚠️ Skill Gaps ({len(missing_skills)}):
{', '.join(missing_skills) if missing_skills else 'None'}

💰 Salary: {job.salary_range}
📍 Location: {job.location} {'(Remote)' if job.remote else '(On-site)'}

Overall Score: {base_score:.1f}%

Recommendation: {"Strong Match!" if base_score >= 80 else "Good Match" if base_score >= 60 else "Moderate Match"}
    '''
    
    return {
        "score": base_score,
        "reasoning": reasoning.strip(),
        "skill_gaps": missing_skills,
        "strengths": matching_skills
    }

@scorer_agent.on_message(model=JobListing)
async def score_compatibility(ctx: Context, sender: str, msg: JobListing):
    ctx.logger.info(f"📥 Scoring: {msg.title}")
    
    analysis = calculate_compatibility_score(msg)
    
    ctx.logger.info(f"📊 Score: {analysis['score']:.1f}%")
    
    match_score = MatchScore(
        job_id=msg.job_id,
        candidate_id=msg.candidate_id,
        title=msg.title,
        company=msg.company,
        match_score=analysis["score"],
        reasoning=analysis["reasoning"],
        skill_gaps=analysis["skill_gaps"],
        strengths=analysis["strengths"],
        salary_range=msg.salary_range,
        location=msg.location,
        remote=msg.remote
    )
    
    if "PUT_AGENT" not in RECOMMENDER_ADDRESS:
        await ctx.send(RECOMMENDER_ADDRESS, match_score)
        ctx.logger.info(f"📤 Score sent to Recommender")
    else:
        ctx.logger.error("❌ RECOMMENDER_ADDRESS not configured!")

@scorer_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 COMPATIBILITY SCORER AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8004")

if __name__ == "__main__":
    scorer_agent.run()