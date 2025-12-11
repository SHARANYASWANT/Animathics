import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

import google.generativeai as genai
from elevenlabs.client import ElevenLabs

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-pro")
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

Topic : {topic}

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

class ConceptAnimation(Scene):
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


