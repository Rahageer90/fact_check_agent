"""
Comprehensive Test Suite for Fact-Check AI Agent

Tests the following:
1. LangChain ReAct agent integration
2. Both MCP tools are called (web_search and news_search)
3. Proper verdict classification (Likely True, Uncertain, Likely False)
4. API response format validation
5. All 4 mandatory test claims
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API keys are configured
def check_api_keys():
    """Verify all required API keys are present"""
    print("\n" + "="*60)
    print("CHECKING API KEYS")
    print("="*60)
    
    required_keys = ["GOOGLE_API_KEY", "SERPAPI_API_KEY", "NEWSAPI_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        if os.getenv(key):
            print(f"✅ {key}: Configured")
        else:
            print(f"❌ {key}: Missing")
            missing_keys.append(key)
    
    if missing_keys:
        print(f"\n⚠️  Missing keys: {', '.join(missing_keys)}")
        print("Please update your .env file with API keys from:")
        print("  - Google: https://aistudio.google.com/")
        print("  - SerpAPI: https://serpapi.com/")
        print("  - NewsAPI: https://newsapi.org/")
        return False
    
    print("\n✅ All API keys are configured!")
    return True


def test_web_search():
    """Test web search MCP tool independently"""
    print("\n" + "="*60)
    print("TEST 1: Web Search Tool")
    print("="*60)
    
    try:
        from mcp_tools.web_search import web_search
        
        test_query = "Is the Earth flat?"
        print(f"\nQuery: '{test_query}'")
        print("Calling web_search()...")
        
        results = web_search(test_query)
        
        print(f"\nResults: {len(results) if isinstance(results, list) else 'N/A'} items")
        if isinstance(results, list) and results:
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')[:70]}...")
        
        print("✅ Web search tool works!")
        return True
    
    except Exception as e:
        print(f"❌ Web search tool failed: {str(e)}")
        return False


def test_news_search():
    """Test news search MCP tool independently"""
    print("\n" + "="*60)
    print("TEST 2: News Search Tool")
    print("="*60)
    
    try:
        from mcp_tools.news_search import news_search
        
        test_query = "OpenAI GPT-4 release"
        print(f"\nQuery: '{test_query}'")
        print("Calling news_search()...")
        
        results = news_search(test_query)
        
        print(f"\nResults: {len(results) if isinstance(results, list) else 'N/A'} items")
        if isinstance(results, list) and results:
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result.get('title', 'N/A')[:70]}...")
        
        print("✅ News search tool works!")
        return True
    
    except Exception as e:
        print(f"❌ News search tool failed: {str(e)}")
        return False


def test_gemini_llm():
    """Test Gemini LLM integration"""
    print("\n" + "="*60)
    print("TEST 3: Gemini LLM Integration")
    print("="*60)
    
    try:
        from services.gemini import get_gemini_llm
        
        print("\nInitializing Gemini LLM...")
        llm = get_gemini_llm()
        
        print("Testing LLM with simple prompt...")
        response = llm.invoke("What is 2+2?")
        
        print(f"Response: {response.content[:100]}...")
        print("✅ Gemini LLM works!")
        return True
    
    except Exception as e:
        print(f"❌ Gemini LLM failed: {str(e)}")
        return False


def test_langchain_tools():
    """Test LangChain tool decorators"""
    print("\n" + "="*60)
    print("TEST 4: LangChain Tool Integration")
    print("="*60)
    
    try:
        from app.agent import web_search, news_search
        
        print("\nVerifying tool decorators...")
        
        # Check if tools have the required attributes
        if hasattr(web_search, 'invoke'):
            print("✅ web_search tool is properly decorated")
        else:
            print("⚠️  web_search missing tool attributes")
        
        if hasattr(news_search, 'invoke'):
            print("✅ news_search tool is properly decorated")
        else:
            print("⚠️  news_search missing tool attributes")
        
        print("✅ LangChain tools are properly integrated!")
        return True
    
    except Exception as e:
        print(f"❌ LangChain tool integration failed: {str(e)}")
        return False


def test_fact_check_agent(claim):
    """Test the main fact-check agent with a specific claim"""
    print(f"\n{'='*60}")
    print(f"Fact-Checking: '{claim}'")
    print("="*60)
    
    try:
        from app.agent import run_fact_check_agent
        
        print("\nRunning ReAct agent...")
        print("(This may take 20-30 seconds...)\n")
        
        result = run_fact_check_agent(claim)
        
        # Validate response structure
        required_fields = ["verdict", "explanation", "sources", "tools_used"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        # Validate verdict classification
        valid_verdicts = ["Likely True", "Uncertain", "Likely False"]
        if result["verdict"] not in valid_verdicts:
            print(f"❌ Invalid verdict: {result['verdict']}")
            print(f"   Valid options: {valid_verdicts}")
            return False
        
        # Validate tools were used
        if "web_search" not in result["tools_used"] or "news_search" not in result["tools_used"]:
            print(f"❌ HARD RULE VIOLATION: Both tools must be called!")
            print(f"   Tools used: {result['tools_used']}")
            return False
        
        # Validate sources format
        if not isinstance(result["sources"], list):
            print(f"❌ Sources must be a list, got {type(result['sources'])}")
            return False
        
        # Print results
        print(f"\n📊 RESULT:")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Tools Used: {', '.join(result['tools_used'])}")
        print(f"   Sources Found: {len(result['sources'])}")
        
        if result["sources"]:
            print(f"\n📚 Top Sources:")
            for i, source in enumerate(result["sources"][:3], 1):
                print(f"   {i}. [{source.get('type', 'unknown').upper()}] {source.get('title', 'N/A')[:60]}...")
        
        print(f"\n💡 Explanation (first 200 chars):")
        print(f"   {result['explanation'][:200]}...")
        
        print(f"\n✅ Fact-check completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Fact-check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "🔍 "*20)
    print("FACT-CHECK AI AGENT - COMPREHENSIVE TEST SUITE")
    print("🔍 "*20)
    
    # Step 1: Check API keys
    if not check_api_keys():
        print("\n❌ Cannot proceed without API keys!")
        return False
    
    # Step 2: Test individual components
    component_tests = [
        ("Web Search Tool", test_web_search),
        ("News Search Tool", test_news_search),
        ("Gemini LLM", test_gemini_llm),
        ("LangChain Tools", test_langchain_tools),
    ]
    
    component_results = {}
    for test_name, test_func in component_tests:
        try:
            component_results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {str(e)}")
            component_results[test_name] = False
    
    # Step 3: Test with mandatory claims
    print("\n" + "="*60)
    print("TESTING MANDATORY CLAIMS (Hard Rule: Both tools must be called)")
    print("="*60)
    
    mandatory_claims = [
        "The Earth is flat.",
        "OpenAI released GPT-4 in 2023.",
        "Drinking bleach can cure COVID-19.",
        "Google is shutting down Gmail in 2025.",
    ]
    
    claim_results = {}
    for i, claim in enumerate(mandatory_claims, 1):
        print(f"\n[CLAIM {i}/{len(mandatory_claims)}]")
        claim_results[claim] = test_fact_check_agent(claim)
    
    # Step 4: Print final report
    print("\n" + "="*60)
    print("FINAL TEST REPORT")
    print("="*60)
    
    print("\n📋 Component Tests:")
    for test_name, passed in component_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n📋 Mandatory Claims:")
    for i, (claim, passed) in enumerate(claim_results.items(), 1):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: Claim {i}")
    
    # Overall result
    all_passed = all(component_results.values()) and all(claim_results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Assignment ready for submission.")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the errors above.")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
