from uagents import Agent, Context, Model
import os
from dotenv import load_dotenv
from config.agent_addresses import CANDIDATE_AGENT_ADDRESS as candidate_agent_address

load_dotenv()

class CandidateProfile(Model):
    candidate_id: str
    resume_text: str
    skills: list
    experience_years: int
    preferences: dict

class RecommendationReport(Model):
    candidate_id: str
    report: str
    top_matches: list



test = Agent(
    name="test",
    port=9000,
    seed="test123",
    endpoint=["http://localhost:9000/submit"]
)

@test.on_event("startup")
async def send(ctx: Context):
    if not candidate_agent_address:
        ctx.logger.error("CANDIDATE_AGENT_ADDRESS not found in environment variables.")
        return

    ctx.logger.info(f"Sending message to: {candidate_agent_address}")

    await ctx.send(
        candidate_agent_address,
        CandidateProfile(
            candidate_id="test_user",
            resume_text="Python ML engineer with 5 years experience",
            skills=["python", "machine learning", "aws", "docker"],
            experience_years=5,
            preferences={"remote": True}
        )
    )

@test.on_message(model=RecommendationReport)
async def receive_report(ctx: Context, sender: str, msg: RecommendationReport):
    ctx.logger.info(f"📩 Received Recommendation Report from {sender}")
    ctx.logger.info(f"Candidate ID: {msg.candidate_id}")
    ctx.logger.info(f"Top Matches: {msg.top_matches}")
    ctx.logger.info(f"Full Report:\n{msg.report}")


test.run()
