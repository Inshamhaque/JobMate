from uagents import Agent, Context

# Import models from centralized models.py
from models import JobListingBatch, RecommendationReport

# 🔗 Replace with actual Candidate Agent address
CANDIDATE_AGENT_ADDRESS = "agent1q08kycnalue0xwhgl888cwlaxlfaqmyyfmzrlvqqpd38c9xh57hlgk893l8"

# Initialize Agent for Agentverse
agent = Agent()

# --------------------------- SCORING ---------------------------

def score_job(job: dict) -> dict:
    """Enhanced scoring based on match score and other factors"""
    score = job.get('match_score', 0.5)
    
    # Bonus for remote positions
    if job.get('remote', False):
        score += 0.1
    
    # Bonus for specified salary
    if job.get('salary', 'Not specified') != "Not specified":
        score += 0.05
    
    return {
        "job": job,
        "final_score": round(min(score, 1.0), 2)
    }

# --------------------------- LEARNING PATH ---------------------------

def generate_learning_path(all_jobs: list) -> str:
    """Generate learning recommendations based on job requirements"""
    
    # Extract all requirements from jobs
    all_requirements = set()
    for job in all_jobs:
        requirements = job.get('requirements', [])
        if requirements:
            all_requirements.update(requirements)
    
    if not all_requirements:
        return "💡 Keep building projects and stay updated with industry trends!"
    
    # Get top 5 most common requirements
    requirement_counts = {}
    for job in all_jobs:
        for req in job.get('requirements', []):
            requirement_counts[req] = requirement_counts.get(req, 0) + 1
    
    sorted_reqs = sorted(requirement_counts.items(), key=lambda x: x[1], reverse=True)
    top_skills = [skill for skill, _ in sorted_reqs[:5]]
    
    if not top_skills:
        return "💡 Focus on deepening your existing skills through real-world projects!"
    
    lines = ["💡 Recommended Learning Path:", ""]
    for i, skill in enumerate(top_skills, 1):
        lines.append(f"{i}. **{skill.title()}** - High demand across {requirement_counts[skill]} job(s)")
    
    lines.append("\n📚 Tip: Build a portfolio project showcasing these skills!")
    
    return "\n".join(lines)

# --------------------------- FINAL REPORT ---------------------------

def create_final_report(scored_jobs: list) -> str:
    """Create personalized job recommendation report"""
    
    if not scored_jobs:
        return "No jobs found matching your profile at the moment. Please try again later!"
    
    # Sort by final score
    sorted_jobs = sorted(scored_jobs, key=lambda x: x["final_score"], reverse=True)
    top_jobs = sorted_jobs[:5]  # Top 5 recommendations
    
    lines = ["🎯 **Your Personalized Job Recommendations**", ""]
    
    for i, item in enumerate(top_jobs, 1):
        job = item["job"]
        score = item["final_score"]
        
        # Format job listing
        remote_badge = "🌍 Remote" if job.get('remote', False) else f"📍 {job.get('location', 'N/A')}"
        
        lines.append(f"**{i}. {job.get('title', 'N/A')}**")
        lines.append(f"🏢 Company: {job.get('company', 'N/A')}")
        lines.append(f"{remote_badge}")
        lines.append(f"💰 Salary: {job.get('salary', 'Not specified')}")
        lines.append(f"⭐ Match Score: {score}/1.0")
        lines.append(f"🔗 Apply: {job.get('url', 'N/A')}")
        lines.append("")
    
    # Add statistics
    avg_score = sum(j["final_score"] for j in top_jobs) / len(top_jobs)
    remote_count = sum(1 for j in top_jobs if j["job"].get('remote', False))
    
    lines.append("---")
    lines.append("")
    lines.append(f"📊 **Summary:**")
    lines.append(f"• Average match score: {avg_score:.2f}/1.0")
    lines.append(f"• Remote positions: {remote_count}/{len(top_jobs)}")
    lines.append(f"• Total jobs found: {len(scored_jobs)}")
    lines.append("")
    
    return "\n".join(lines)

# --------------------------- MESSAGE HANDLER ---------------------------

@agent.on_message(model=JobListingBatch)
async def handle_job_batch(ctx: Context, sender: str, msg: JobListingBatch):
    """Handle incoming job batch"""
    
    candidate_id = msg.candidate_id
    jobs = msg.jobs
    total_count = msg.total_count
    
    ctx.logger.info(f"📦 Received batch for {candidate_id[:16]}...")
    ctx.logger.info(f"📊 Total jobs in batch: {total_count}")
    
    if not jobs:
        ctx.logger.warning(f"⚠️ Empty job batch for {candidate_id}")
        return
    
    # Log received jobs
    for i, job in enumerate(jobs[:5], 1):
        ctx.logger.info(
            f"💼 [{i}] {job.get('title', 'N/A')} @ {job.get('company', 'N/A')} "
            f"(Score: {job.get('match_score', 0):.2f})"
        )
    
    if len(jobs) > 5:
        ctx.logger.info(f"   ... and {len(jobs) - 5} more jobs")
    
    # Score all jobs
    ctx.logger.info(f"🎯 Scoring {len(jobs)} jobs...")
    scored_jobs = [score_job(job) for job in jobs]
    
    # Create main report
    ctx.logger.info(f"📝 Creating recommendation report...")
    report_text = create_final_report(scored_jobs)
    
    # Add learning path
    report_text += "\n\n" + generate_learning_path(jobs)
    
    # Add footer
    report_text += "\n\n---\n📈 **Next Steps:** Review these opportunities and tailor your applications to each company's needs!"
    
    # Extract top job titles
    top_job_titles = [job.get('title', 'N/A') for job in jobs[:5]]
    
    # Create report model
    report = RecommendationReport(
        candidate_id=candidate_id,
        report=report_text,
        top_matches=top_job_titles
    )
    
    # Send report
    try:
        await ctx.send(CANDIDATE_AGENT_ADDRESS, report)
        ctx.logger.info(f"✅ Report sent to Candidate Agent for {candidate_id[:16]}...")
    except Exception as e:
        ctx.logger.error(f"❌ Failed to send report: {e}")

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("="*70)
    ctx.logger.info("🚀 RECOMMENDATION AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"⚙️ Processing Mode: Batch (entire job list at once)")
    ctx.logger.info(f"📤 Sends reports to: {CANDIDATE_AGENT_ADDRESS}")
    ctx.logger.info("="*70)

if __name__ == "__main__":
    agent.run()
