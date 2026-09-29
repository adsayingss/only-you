# A Little Story: Web Edition

This static HTML, CSS, and JavaScript version runs in modern browsers and can be hosted from this folder on GitHub Pages. It has no build step, server, or dependencies. The original Python/Pygame project remains at the repository root.

## Run locally

Open `index.html` in Chrome, Firefox, Safari, or Edge. Select **Begin our story** to start the music and story together; browsers require a user gesture before playing audio. Keep `assets/moonlit_score.wav` alongside the HTML file so the soundtrack can load.

## Deploy on GitHub Pages

1. Push the repository, including the `web/` folder, to GitHub.
2. Open the repository's **Settings → Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Select the branch containing the project and set the folder to **/web**.
5. Save. When deployment completes, open the Pages URL shown in the settings.

The Pages source folder must contain `index.html` at its top level. CSS, JavaScript, and soundtrack paths are relative, so they work locally and under a GitHub Pages project URL. No Jekyll configuration is needed.

## Controls

- Select **Begin our story** to start the film and soundtrack.
- Select **Skip story** or press Space to move to the next beat.
- Select the music control to pause or resume the soundtrack.
- Select **YES** or press Y / Enter to play the ending.

The final choice launches fireworks, hearts, petals, and confetti. The ending remains on screen after the animation.