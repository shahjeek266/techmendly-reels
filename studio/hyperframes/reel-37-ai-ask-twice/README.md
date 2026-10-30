Motion-graphic Reel built with HyperFrames (https://github.com/heygen-com/hyperframes).
gen.py makes the Kokoro voice + audio (needs ~/kokoro), mk.py + style.css write index.html (GSAP timeline),
then: npx hyperframes@0.8.221 render -o out.mp4  (GSAP must be at assets/gsap.min.js; set HYPERFRAMES_BROWSER_PATH if Chrome can't be downloaded).
