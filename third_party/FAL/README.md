# Consistent image pipeline for narrated video (Claude + Flux/fal.ai)

Shows how to replace an all-in-one AI content subscription with a minimal,
reproducible pipeline for narrated, image-driven video series:

1. Claude breaks a narration script into structured, per-scene image prompts
   (via tool use), sharing one style descriptor across all scenes.
2. Flux (via fal.ai) renders each scene with a deterministic per-scene seed,
   so re-generating a single scene later doesn't visually drift from the rest.
3. A simple cost comparison shows real pay-as-you-go spend versus a typical
   bundled subscription tier.

See `consistent_image_pipeline_for_narrated_video.ipynb`.

**Requirements:** an `ANTHROPIC_API_KEY` and a `FAL_KEY` (fal.ai, pay-as-you-go).
