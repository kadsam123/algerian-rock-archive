import google.generativeai as genai

# --- PASTE YOUR KEY INSIDE THE QUOTES BELOW ---
api_key = "AIzaSyClYvVCohsCwxmaqPFK2BrjizY9H3pubZE"
# ----------------------------------------------

genai.configure(api_key=api_key)

print("\n🔍 CHECKING AVAILABLE MODELS...")
try:
    available = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ AVAILABLE: {m.name}")
            available = True
    
    if not available:
        print("❌ No text generation models found. Check API Key permissions.")
        
except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")

print("\nDone.")