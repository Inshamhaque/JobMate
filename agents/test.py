"""
Test Agent - Sends PDF resumes to Candidate Profile Agent
"""

from uagents import Agent, Context
import os
from dotenv import load_dotenv
from config.agent_addresses import CANDIDATE_AGENT_ADDRESS as candidate_agent_address
import base64

# Import shared models
from agents.models import PDFResume, RecommendationReport

load_dotenv()

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

test = Agent(
    name="test",
    port=9000,
    seed="test123",
    endpoint=["http://localhost:9000/submit"]
)

# ============================================================================
# STARTUP HANDLER - SEND PDF
# ============================================================================

@test.on_event("startup")
async def send(ctx: Context):
    """Send PDF resume on startup"""
    
    # Check if candidate agent address is configured
    if not candidate_agent_address:
        ctx.logger.error("❌ CANDIDATE_AGENT_ADDRESS not found in environment variables.")
        ctx.logger.error("   Please set it in config/agent_addresses.py")
        return
    
    if "PUT_YOUR" in candidate_agent_address:
        ctx.logger.error("❌ CANDIDATE_AGENT_ADDRESS not properly configured!")
        ctx.logger.error("   Please update config/agent_addresses.py with the actual agent address")
        return
    
    ctx.logger.info("="*70)
    ctx.logger.info("📤 SENDING PDF RESUME TO CANDIDATE AGENT")
    ctx.logger.info("="*70)
    ctx.logger.info(f"Target Agent: {candidate_agent_address}")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, "Inshamul_Haque.pdf")
    
    # Debug information
    ctx.logger.info(f"Script directory: {script_dir}")
    ctx.logger.info(f"Looking for PDF at: {pdf_path}")
    ctx.logger.info(f"Current working directory: {os.getcwd()}")
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        ctx.logger.error(f"❌ PDF file not found at: {pdf_path}")
        ctx.logger.info(f"📂 Files in script directory:")
        try:
            files = os.listdir(script_dir)
            for file in files:
                ctx.logger.info(f"   - {file}")
        except Exception as e:
            ctx.logger.error(f"   Could not list files: {e}")
        return
    
    # Read and encode PDF
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        ctx.logger.info(f"✅ PDF file loaded: {len(pdf_bytes)} bytes")
        
        # Encode PDF as base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        ctx.logger.info(f"✅ PDF encoded to base64: {len(pdf_base64)} characters")
        
        # Create and send PDFResume message
        pdf_message = PDFResume(
            filename="Inshamul_Haque.pdf",
            content=pdf_base64,
            candidate_name="Inshamul Haque"
        )
        
        await ctx.send(candidate_agent_address, pdf_message)
        
        ctx.logger.info("✅ PDF resume sent successfully!")
        ctx.logger.info("="*70)
        ctx.logger.info("⏳ Waiting for response from Candidate Agent...")
        ctx.logger.info("="*70 + "\n")
        
    except Exception as e:
        ctx.logger.error(f"❌ Error processing PDF: {type(e).__name__}: {e}")
        import traceback
        ctx.logger.error(traceback.format_exc())

# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

@test.on_message(model=RecommendationReport)
async def receive_report(ctx: Context, sender: str, msg: RecommendationReport):
    """Handle recommendation reports from the system"""
    ctx.logger.info("="*70)
    ctx.logger.info("📩 RECEIVED RECOMMENDATION REPORT")
    ctx.logger.info("="*70)
    ctx.logger.info(f"From: {sender}")
    ctx.logger.info(f"Candidate ID: {msg.candidate_id}")
    ctx.logger.info(f"\n📊 Top Matches ({len(msg.top_matches)}):")
    for i, match in enumerate(msg.top_matches, 1):
        ctx.logger.info(f"   {i}. {match}")
    ctx.logger.info(f"\n📄 Full Report:")
    ctx.logger.info(f"{msg.report}")
    ctx.logger.info("="*70 + "\n")

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@test.on_event("startup")
async def startup_message(ctx: Context):
    """Display startup information"""
    ctx.logger.info("\n" + "="*70)
    ctx.logger.info("🧪 TEST AGENT STARTED")
    ctx.logger.info("="*70)
    ctx.logger.info(f"📍 Agent Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 9000")
    ctx.logger.info(f"🎯 Target: {candidate_agent_address if candidate_agent_address else 'NOT CONFIGURED'}")
    ctx.logger.info("="*70 + "\n")

# ============================================================================
# RUN AGENT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEST AGENT - PDF RESUME SENDER")
    print("="*70 + "\n")
    test.run()