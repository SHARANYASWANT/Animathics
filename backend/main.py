import glob
import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
import uuid
import subprocess
from pydantic import BaseModel
from elevenlabs import save

load_dotenv()

class PromptRequest(BaseModel):
    prompt: str

class AudioRequest(BaseModel):
    text: str

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")
print("Gemini initialized successfully.")

try:
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    print("ElevenLabs initialized successfully.")
except Exception as e:
    print(f"⚠️ WARNING: ElevenLabs initialization failed → {e}")
    elevenlabs_client = None

app = FastAPI(title="Animathics", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEOS_DIR = "videos"
AUDIO_DIR = "audio"
SCRIPTS_DIR = "temp_scripts"
SUBTITLES_DIR = "subtitles"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(SUBTITLES_DIR, exist_ok=True)

app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/subtitles", StaticFiles(directory=SUBTITLES_DIR), name="subtitles")

@app.get("/")
def read_root():
    return {
        "server_status": "online",
        "gemini_status": "ready",
        "elevenlabs_status": "enabled" if elevenlabs_client else "disabled",
        "storage": {
            "videos": VIDEOS_DIR,
            "audio": AUDIO_DIR,
            "scripts": SCRIPTS_DIR,
            "subtitles": SUBTITLES_DIR,
        }
    }

def build_gemini_prompt(topic: str) -> str:
        return f"""
You are an EXPERT MANIM COMMUNITY ANIMATOR. Generate ZERO-ERROR animations using ONLY verified Manim Community Edition syntax. Every line must execute perfectly without compilation errors.

"Concept Title" → "{topic}" 

## 🚫 ABSOLUTE FORBIDDEN ELEMENTS

*NEVER USE THESE:*
- ❌ from manimgl import * or ANY ManimGL syntax
- ❌ Custom classes like Checkmark, CustomShape without proper definition
- ❌ .get_corner() without direction parameter
- ❌ Interactive widgets or real-time manipulations
- ❌ Deprecated functions from older Manim versions
- ❌ Complex custom VMobject classes
- ❌ Browser-based outputs or OpenGL renderers
- ❌ Methods that don't exist in Community Edition
- ❌ List arithmetic (e.g., A + 0.5 * (B - A) where A, B are lists)
- ❌ Mixing VMobject and Mobject in VGroup
- ❌ Elements extending beyond screen boundaries
- ❌ Overlapping text or objects

## ✅ MANDATORY REQUIREMENTS

### *1. IMPORTS - ONLY THIS:*
```python
from manim import *
import numpy as np  # Only if needed for calculations
```

### *2. VERIFIED BASIC SHAPES ONLY:*
```python
# USE THESE BUILT-IN SHAPES ONLY:
# Circle()
# Square() 
# Rectangle()
# Triangle()
# Line()
# Arrow()
# Dot()
# Polygon([points])  # For custom shapes

# NEVER create custom VMobject classes unless absolutely necessary
# ALWAYS use np.array() for coordinate calculations
```

### *3. POSITION SYSTEM - SAFE COORDINATES:*
```python
# SCREEN BOUNDARIES (NEVER EXCEED):
# MAX_X = 5.5    # Left/Right limit (safe zone)
# MAX_Y = 2.8    # Up/Down limit (safe zone)

# COORDINATE CALCULATIONS - ALWAYS USE np.array():
# A = np.array([0, 0, 0])              # Origin point
# B = np.array([2, 1, 0])              # Example point
# C = A + 0.5 * (B - A)                # Correct vector math

# SAFE POSITIONING METHODS:
# obj.move_to(ORIGIN)                    # Center
# obj.to_edge(UP, buff=0.8)             # Top edge with buffer
# obj.to_edge(DOWN, buff=0.8)           # Bottom edge with buffer  
# obj.to_edge(LEFT, buff=0.8)           # Left edge with buffer
# obj.to_edge(RIGHT, buff=0.8)          # Right edge with buffer
# obj.next_to(other_obj, UP, buff=0.4)  # Relative positioning
# obj.shift(UP * 1.5)                   # Relative movement (within bounds)

# PREVENT OVERLAPPING:
# obj1.move_to(LEFT * 2)               # Left position
# obj2.move_to(RIGHT * 2)              # Right position (no overlap)
# obj3.move_to(UP * 1.5)               # Top position
# obj4.move_to(DOWN * 1.5)             # Bottom position
```

### *4. TEXT AND MATH - SIMPLE ONLY:*
```python
# TEXT (ALWAYS WORKS):
# title = Text("Title Here", font_size=48)
# subtitle = Text("Subtitle", font_size=32)

# MATH - SIMPLE EXPRESSIONS ONLY:
# equation = MathTex(r"x^2 + y^2 = r^2")
# formula = MathTex(r"f(x) = 2x + 1")

# AVOID: Complex LaTeX, special symbols, or advanced formatting
```

### *5. COLORS - BUILT-IN ONLY:*
```python
# USE THESE COLORS ONLY:
# RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, PINK
# WHITE, BLACK, GRAY, LIGHT_GRAY, DARK_GRAY
```

### *6. AXES AND GRAPHS - VERIFIED TEMPLATE:*
```python
# SAFE AXES CONFIGURATION:
# axes = Axes(
#     x_range=[-4, 4, 1],
#     y_range=[-3, 3, 1],
#     x_length=8,
#     y_length=6,
#     tips=False  # Avoid tip issues
# )

# SIMPLE FUNCTION PLOTTING:
# curve = axes.plot(lambda x: x**2, x_range=[-2, 2], color=BLUE)

#Mandatory alignment : Always center and doesnot goes out of layout (text, shapes, other things) focus on center alignment without overlapping and the value should be relative to the topics dont be hardcoded.
```

## 🏗 MANDATORY SCENE STRUCTURE

```python
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Step 1: Create title
        self.create_title()
        self.wait(1)
        
        # Step 2: Main content
        self.show_main_content()
        self.wait(1)
        
        # Step 3: Clear and conclude
        self.clear_screen()
        self.create_conclusion()
        self.wait(2)
    
    def create_title(self):
        title = Text("Concept Title", font_size=48, color=BLUE)
        title.to_edge(UP, buff=0.8)
        self.play(Write(title), run_time=2)
        self.title = title
    
    def show_main_content(self):
        # Your main animation code here
        # Use only verified elements
        pass
    
    def clear_screen(self):
        # Remove all objects safely
        self.play(FadeOut(VGroup(*self.mobjects)), run_time=1)
        self.wait(0.5)
    
    def create_conclusion(self):
        conclusion = Text("Conclusion", font_size=36, color=GREEN)
        conclusion.move_to(ORIGIN)
        self.play(Write(conclusion), run_time=1.5)
```

## 🔧 ERROR PREVENTION RULES

### *Rule 1: Method Verification*
```python
# CORRECT: Always provide required parameters
# corner = square.get_corner(UP + RIGHT)  # Direction required

# WRONG: Missing parameters
# corner = square.get_corner()  # Will cause error
```

### *Rule 2: VGroup for VMobjects Only*
```python
# CORRECT: Only VMobjects in VGroup
# shapes = VGroup(circle, square, triangle)  # All VMobjects
# self.play(Create(shapes), run_time=2)

# CORRECT: Mixed types - use Group instead
# from manim import Group
# mixed_objects = Group(*self.mobjects)  # For mixed Mobject types
# self.play(FadeOut(mixed_objects), run_time=1)

# WRONG: Mixing VMobject and Mobject in VGroup
# objects = VGroup(*self.mobjects)  # May cause TypeError
```

### *Rule 3: Simple Animations Only*
```python
# SAFE ANIMATIONS:
# self.play(Create(obj), run_time=2)
# self.play(Write(text), run_time=1.5)
# self.play(Transform(obj1, obj2), run_time=2)
# self.play(FadeIn(obj), run_time=1)
# self.play(FadeOut(obj), run_time=1)
# self.play(obj.animate.shift(UP), run_time=1)

# AVOID: Complex custom animations
```

### *Rule 4: Screen Layout Management*
```python
# TITLE AREA (Top 15% of screen):
# title.to_edge(UP, buff=0.8)           # Safe title position

# MAIN CONTENT AREA (Middle 70% of screen):
# content.move_to(ORIGIN)               # Center for main content
# left_content.move_to(LEFT * 3)        # Left side content
# right_content.move_to(RIGHT * 3)      # Right side content

# FOOTER AREA (Bottom 15% of screen):
# footer.to_edge(DOWN, buff=0.8)        # Safe footer position

# PREVENT OVERLAPPING - Minimum spacing:
# MIN_SPACING = 0.5                     # Minimum distance between objects
# obj2.next_to(obj1, RIGHT, buff=MIN_SPACING)

# GRID LAYOUT for multiple objects:
# objects = [obj1, obj2, obj3, obj4]
# positions = [LEFT*2 + UP, RIGHT*2 + UP, LEFT*2 + DOWN, RIGHT*2 + DOWN]
# for obj, pos in zip(objects, positions):
#     obj.move_to(pos)
```

## 📝 VERIFIED TEMPLATES
"""

def clean_manim_code(manim_code: str) -> str:
    manim_code = re.sub(r"^```(?:python)?", "", manim_code, flags=re.MULTILINE)
    manim_code = re.sub(r"```$", "", manim_code, flags=re.MULTILINE).strip()

    manim_code = manim_code.replace(r"\c", r"\\c")

    manim_code = re.sub(r"class\s+\w+\s*\(", "class GeneratedScene(", manim_code)

    if "class GeneratedScene" in manim_code and "Scene" not in manim_code.split("class GeneratedScene")[1]:
        manim_code = manim_code.replace("class GeneratedScene(", "class GeneratedScene(Scene):")

    if "class GeneratedScene" not in manim_code:
        manim_code = (
            "from manim import *\n\n"
            "class GeneratedScene(Scene):\n"
            "    def construct(self):\n"
            "        self.add(Text('Error: Scene could not be generated'))\n"
        )

    return manim_code

def build_alignment_prompt(manim_code: str) -> str:
    return f"""
You are a MANIM COMMUNITY ALIGNMENT SPECIALIST - An expert code debugger focused exclusively on fixing positioning, spacing, and overlap issues in Manim Community scripts.

**YOUR MISSION:**
Analyze the provided Manim Community script and fix ALL alignment problems while preserving the original animation logic and educational content.

**ALIGNMENT PROBLEMS TO DETECT & FIX:**

1. **OVERLAPPING ELEMENTS:**
   - Text overlapping with other text
   - Objects overlapping with axes/grids
   - Labels covering important visual elements
   - Mathematical expressions overlapping boundaries

2. **SCREEN BOUNDARY VIOLATIONS:**
   - Elements extending beyond visible screen area
   - Text cut off at screen edges
   - Objects positioned outside safe zones
   - Coordinate system exceeding display limits

3. **SPACING INCONSISTENCIES:**
   - Inconsistent buffer distances between elements
   - Poor vertical/horizontal spacing patterns
   - Elements too close for readability
   - Uneven distribution of screen space

4. **POSITIONING ERRORS:**
   - Incorrect use of .to_edge(), .next_to(), .move_to()
   - Missing or incorrect buff parameters
   - Wrong directional constants (UP, DOWN, LEFT, RIGHT)
   - Improper center positioning

**FIXING METHODOLOGY:**

**STEP 1: SCREEN BOUNDARY ANALYSIS**
```python
# DEFINE SAFE ZONES (DO NOT EXCEED THESE LIMITS)
SCREEN_WIDTH = 14.2    # Total usable width
SCREEN_HEIGHT = 8.0    # Total usable height
SAFE_LEFT = LEFT * 6.5   # Safe left boundary  
SAFE_RIGHT = RIGHT * 6.5 # Safe right boundary
SAFE_UP = UP * 3.5      # Safe top boundary
SAFE_DOWN = DOWN * 3.5  # Safe bottom boundary
TITLE_ZONE = UP * 3.2   # Reserved for titles
FOOTER_ZONE = DOWN * 3.2 # Reserved for footers
CENTER_ZONE = ORIGIN    # Safe center area
STEP 2: ELEMENT POSITIONING CORRECTION
python# CORRECTED POSITIONING PATTERNS
# Replace problematic positioning with these tested patterns:

# TITLES - Always safe at top
title.to_edge(UP, buff=0.5)

# SUBTITLES - Proper spacing from title  
subtitle.next_to(title, DOWN, buff=0.3)

# MAIN CONTENT - Center positioning
content.move_to(ORIGIN)

# SIDE LABELS - Safe edge positioning
left_label.to_edge(LEFT, buff=0.8)
right_label.to_edge(RIGHT, buff=0.8)

# EQUATIONS - Vertical stacking with proper spacing
eq1.move_to(UP * 2)
eq2.next_to(eq1, DOWN, buff=0.5)
eq3.next_to(eq2, DOWN, buff=0.5)

# COORDINATE SYSTEMS - Screen-safe dimensions
axes = Axes(
    x_range=[-4, 4, 1],    # Safe range
    y_range=[-3, 3, 1],    # Safe range  
    x_length=8,            # Safe width
    y_length=6,            # Safe height
)
STEP 3: OVERLAP ELIMINATION
python# SPACING RULES TO APPLY:

# MINIMUM BUFFERS
TIGHT_SPACING = 0.2   # Between closely related elements
NORMAL_SPACING = 0.4  # Standard element separation
LOOSE_SPACING = 0.8   # Between different sections
SECTION_SPACING = 1.2 # Between major scene components

# VERTICAL STACKING - No overlaps
element1.to_edge(UP, buff=0.6)
element2.next_to(element1, DOWN, buff=NORMAL_SPACING)
element3.next_to(element2, DOWN, buff=NORMAL_SPACING)

# HORIZONTAL ARRANGEMENT - Proper distribution  
left_element.to_edge(LEFT, buff=1.0)
center_element.move_to(ORIGIN)
right_element.to_edge(RIGHT, buff=1.0)

# LABEL POSITIONING - Clear of main objects
label.next_to(object, UP + RIGHT, buff=0.3)  # Diagonal positioning
label.next_to(object, DOWN + LEFT, buff=0.3)  # Alternative diagonal
STEP 4: RESPONSIVE POSITIONING
python# ADAPTIVE POSITIONING - Elements adjust to content
# Replace fixed coordinates with relative positioning:

# WRONG:
text.move_to([2, 1, 0])  # Fixed coordinates can overlap

# CORRECT:
text.next_to(reference_object, RIGHT, buff=0.5)  # Relative positioning

# WRONG: 
equation.shift(UP * 3)  # May go off-screen

# CORRECT:
equation.to_edge(UP, buff=0.8)  # Screen-safe positioning
MATHEMATICAL CONTENT ALIGNMENT:
python# EQUATION SYSTEMS - Proper alignment
system_title = Text("System of Equations")
system_title.to_edge(UP, buff=0.5)

eq1 = MathTex("2x + 3y = 7")
eq1.next_to(system_title, DOWN, buff=0.8)
eq1.to_edge(LEFT, buff=2.0)

eq2 = MathTex("x - y = 1") 
eq2.next_to(eq1, DOWN, buff=0.4)
eq2.align_to(eq1, LEFT)  # Align left edges

# COORDINATE SYSTEMS - Safe positioning
axes.move_to(ORIGIN)
axes.shift(DOWN * 0.5)  # Leave room for top labels

# FUNCTION LABELS - Clear positioning
func_label = MathTex("f(x) = x^2")
func_label.next_to(axes, UP, buff=0.3)
func_label.to_edge(LEFT, buff=1.0)
CRITICAL FIXES TO IMPLEMENT:

REPLACE ALL HARDCODED COORDINATES:

python# WRONG:
text.move_to([3, 2.5, 0])

# FIXED:
text.to_edge(UP, buff=0.8).shift(RIGHT * 2)

ADD MISSING BUFFERS:

python# WRONG:
label.next_to(point)

# FIXED: 
label.next_to(point, UP, buff=0.3)

CORRECT SCREEN VIOLATIONS:

python# WRONG:
title.move_to(UP * 4)  # Beyond screen

# FIXED:
title.to_edge(UP, buff=0.5)  # Safe positioning

FIX OVERLAPPING GROUPS:

python# WRONG:
group1.move_to(ORIGIN)
group2.move_to(ORIGIN)  # Overlap!

# FIXED:
group1.move_to(UP * 1.5)
group2.move_to(DOWN * 1.5)
TESTING VERIFICATION:
After each fix, ensure:
✅ All elements visible on screen
✅ No overlapping text or objects
✅ Consistent spacing throughout
✅ Labels clearly readable
✅ Mathematical expressions properly aligned
✅ Coordinate systems within bounds
✅ Scene transitions maintain positioning
OUTPUT REQUIREMENTS:

Return COMPLETE corrected Manim script
{manim_code}
--- CODE END ---
"""
def enforce_alignment_with_gemini(manim_code: str) -> str:
    try:
        prompt = build_alignment_prompt(manim_code)
        response = gemini_model.generate_content(prompt)  
        fixed_code = clean_manim_code(response.text or manim_code)
        return fixed_code
    except Exception as e:
        print(f"[Alignment Gemini] Failed: {e}")
        return manim_code  

def build_fix_prompt(original_code: str, error_output: str, topic: str) -> str:
    safe_original = original_code if original_code else "NO_ORIGINAL_CODE_PROVIDED"
    safe_error = error_output if error_output else "NO_ERROR_OUTPUT_PROVIDED"
    return f"""
You are an EXPERT MANIM COMMUNITY ANIMATOR tasked with FIXING the following Manim Community Edition script so it runs without errors (v0.19.0 compatible).
Topic: {topic}

--- ORIGINAL CODE START ---
{safe_original}
--- ORIGINAL CODE END ---

--- ERROR OUTPUT START ---
{safe_error}
--- ERROR OUTPUT END ---

Instructions:
1. Return ONLY the corrected Python code. No explanations, no markdown, no extra text.
2. Ensure the scene class is named GeneratedScene and inherits from Scene.
3. Use only verified Manim CE functions and patterns. Avoid deprecated or custom VMobject classes.
4. Keep layouts inside safe boundaries: MAX_X=5.5, MAX_Y=2.8 and use move_to/next_to/to_edge patterns.
5. Keep animations simple and robust (Create, Write, FadeIn, FadeOut, Transform).
6. If you modify imports or add helper functions, include them at top of the script.
7. End with a final wait (self.wait(1) or greater).
8. Do not attempt to run manim or reference local file paths.
"""

@app.post("/generate-audio")
def generate_audio(request: AudioRequest):
    if not elevenlabs_client:
        raise HTTPException(status_code=503, detail="Audio generation is disabled.")
    try:
        audio = elevenlabs_client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM", 
            model_id="eleven_multilingual_v2",
            text=request.text
        )
        audio_filename = f"audio_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join("audio", audio_filename)
        save(audio, audio_path)
        audio_url = f"http://localhost:8000/audio/{audio_filename}"
        return {"audioUrl": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {e}")

@app.post("/generate-video")
def generate_video(request: PromptRequest):
    prompt = request.prompt.strip().lower()
    print(f"Prompt received: {prompt}")
    gemini_prompt = build_gemini_prompt(prompt)

    try:
        response = gemini_model.generate_content(gemini_prompt)
        initial_text = response.text or ""
    except ValueError as e:
        print(f"Error getting initial response from Gemini: {e}")
        raise HTTPException(status_code=500, detail="The AI model returned an empty or invalid response. This might be due to a safety filter. Please try a different prompt.")

    parts = initial_text.split("---TIMED_TRANSCRIPT_START---")
    manim_code = clean_manim_code(parts[0].strip())
    manim_code= enforce_alignment_with_gemini(manim_code)
    transcript = parts[1].strip() if len(parts) > 1 else f"Step-by-step explanation for {prompt}"
    if not transcript.strip():
        transcript = f"This video explains {prompt} step by step."


    script_filename = os.path.join(SCRIPTS_DIR, f"video_{uuid.uuid4().hex}.py")
    with open(script_filename, "w") as f:
        f.write(manim_code)
    print(f"Saved initial Manim code to {script_filename}")

    max_retries = 5
    attempt = 0
    last_error_output = ""
    final_video_path = None

    while attempt <= max_retries:
        attempt += 1
        print(f"Rendering attempt {attempt} for {script_filename}")
        try:
            proc = subprocess.run(
                ["manim", "-pql", script_filename, "GeneratedScene"],
                check=False,
                capture_output=True,
                text=True
            )

            if proc.returncode == 0:
                script_name_without_ext = os.path.splitext(os.path.basename(script_filename))[0]

                possible_videos = glob.glob(
                    f"media/videos/{script_name_without_ext}/**/GeneratedScene.mp4",
                    recursive=True
                )

                if possible_videos:
                    manim_video_path = possible_videos[0]

                    final_video_name = f"{script_name_without_ext}.mp4"
                    final_path = os.path.join(VIDEOS_DIR, final_video_name)

                    if os.path.exists(final_path):
                        os.remove(final_path)

                    os.rename(manim_video_path, final_path)
                    final_video_path = final_path

                    # cleanup temp script
                    try:
                        os.remove(script_filename)
                    except Exception:
                        pass

                    video_url = f"http://localhost:8000/videos/{final_video_name}"

                    try:
                        audio_response = generate_audio(AudioRequest(text=transcript))
                        audio_url = audio_response["audioUrl"]
                    except HTTPException as e:
                        print(f"Audio generation failed: {e.detail}")
                        audio_url = None

                    return {
                        "videoUrl": video_url,
                        "audioUrl": audio_url,
                        "transcript": transcript,
                        "title": f"Explaining {prompt}"
                    }
                else:
                    last_error_output = "Rendering succeeded but video file could not be located."
                    print(last_error_output)

            else:
                last_error_output = f"Return code: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
                print(f"Render failed with error:\n{last_error_output}")

        except subprocess.CalledProcessError as e:
            last_error_output = f"CalledProcessError: {e}"
            print(last_error_output)

        if attempt <= max_retries:
            print(f"Requesting Gemini to fix code (attempt {attempt})")
            fix_prompt = build_fix_prompt(manim_code, last_error_output, prompt)
            fix_response = gemini_model.generate_content(fix_prompt)
            fixed_text = fix_response.text or ""
            fixed_code = clean_manim_code(fixed_text.strip())
            try:
                with open(script_filename, "w") as f:
                    f.write(fixed_code)
                manim_code = fixed_code
                print(f"Saved fixed Manim code to {script_filename} (attempt {attempt})")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to write fixed script: {e}")
        else:
            break

    try:
        if os.path.exists(script_filename):
            os.remove(script_filename)
    except Exception:
        pass

    raise HTTPException(status_code=500, detail=f"Failed to generate video after {max_retries + 1} attempts. Last error: {last_error_output}")
