import pytest
import os
from src.mcp.gmail_parser import gmail_parser

@pytest.mark.asyncio
async def test_gmail_mcp_extracts_rewards_from_eml():
    """
    Test Case: Verify reward extraction accuracy from sample EML files.
    AAA Pattern.
    """
    # 1. Arrange: Read sample EML file
    eml_path = os.path.join(os.path.dirname(__file__), "data/samples/reward_points.eml")
    with open(eml_path, "r") as f:
        eml_content = f.read()
        
    # extract_with_llm is designed to process text snippets from the Gmail API, 
    # but our EML file contains the same data.
    
    # 2. Act: Extract entities
    analysis = await gmail_parser.extract_with_llm(eml_content)
    
    # 3. Assert: Verify 100% accuracy in extraction
    assert analysis["classification"] == "REWARD"
    assert analysis["extracted_entities"]["points_value"] == 50000
    assert analysis["extracted_entities"]["program"] == "Chase Sapphire"
    print("Gmail MCP Reward Extraction Verified.")
