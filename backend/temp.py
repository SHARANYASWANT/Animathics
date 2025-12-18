import google.generativeai as genai

# Configure your API key
genai.configure(api_key="AIzaSyApenWcAgNvl1p1KyYARA4Dd46Rn8iBBTY")

# List all models that support the 'generateContent' method
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model Name: {m.name}")