# A Little Story — a cinematic proposal game

A custom-drawn Pygame mini love story, built from layered city-night scenery, hand-drawn characters, camera movement, glowing hearts, fireworks, falling petals, and original procedural audio. It runs as a 1280 × 720 fullscreen experience at 60 FPS; there are no Tkinter windows or standard GUI widgets.

## Run on Windows

1. Install Python 3.10+.
2. Open this folder in VS Code.
3. In the integrated terminal, install the dependency:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Start the game with **Run Python File** on `main.py`, or:

   ```powershell
   python main.py
   ```

## Personalize it

Edit the four constants near the top of `main.py`:

- `BOY_NAME` — his name in the story.
- `GIRL_NAME` — her name in the story.
- `PROPOSAL_MESSAGE` — the central proposal line.
- `MUSIC_FILE` — the optional custom MP3 filename (defaults to `romantic_music.mp3`).

Put your own soundtrack MP3 beside `main.py`. Music playback starts automatically. If `romantic_music.mp3` is not found, the game automatically uses the first MP3 in the project folder. If no MP3 is present, it shows a setup note and generates/plays an original soft instrumental WAV under `assets/`, so the full story remains playable. If an audio device cannot initialize, the story still runs and shows a clear notice.

## Controls

- Click **YES** or **ABSOLUTELY**, or press **1/Y** or **2/A**, at the proposal to choose an ending.
- Press **+ / Up** to raise music volume; **- / Down** to lower it.
- **Space** skips the current timed beat when it is skippable.
- **F11** toggles fullscreen; **Esc** exits fullscreen (press it again while windowed to close); **Q** closes immediately.

The opening, first-sight scene, five-scene montage, heart-light effect, animated walk and kneel, ring reveal, proposal pause, fireworks, and personalized ending play in sequence.

## Files

- `main.py` — Pygame renderer, story timeline, animation, controls, and generated fallback soundtrack.
- `requirements.txt` — Pygame CE dependency; Pygame CE provides the `pygame` module and Windows wheels.
- `.vscode/launch.json` — VS Code launch profile.
