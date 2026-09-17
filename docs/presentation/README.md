# SymbolicRCA hackathon presentation

Open `index.html` directly in a browser. No build step, network access, or external dependencies are required.

Nine slides cover the problem, symbolic evidence, proposed architecture, an OpenRCA comparison, documented implementation status, evaluation plan, future work, and broader research direction. Content and status reflect the repository documents read on September 17, 2026; refresh the status and evaluation slides before presenting new results.

## Controls

- Arrow keys, Space, Page Up / Page Down: move between slides.
- Home / End: first / last slide.
- N: toggle speaker notes and source links. Notes are visible on the same screen, so close them before presenting.
- F: toggle full screen where supported.
- Browser Print: export all slides to PDF in landscape slide format, without controls or notes. Enable background graphics and disable browser headers and footers.
- Link to a slide with `index.html#slide-8`.

## Editing

Edit slide text and speaker notes in `index.html`, styling in `styles.css`, and navigation in `slides.js`. Each slide is a semantic HTML section. Keep IDs sequential when adding slides; the counter updates automatically. Without JavaScript, slides remain readable as a scrolling document.

The design adapts the selected **Project Kickoff** template's dark green background, lime headings, centered cover, and text-column layouts to HTML. Inter uses a local installation when available, with Arial/Helvetica fallbacks. This is an HTML adaptation, not a PowerPoint conversion.

Sources are linked in each slide's speaker notes. Future-work ideas are collected in [the running list](../hackathon-future-work.md); update its presentation summary on slide 8 as ideas evolve. Performance gains are research hypotheses until measured.

## Diagrams

Slides 2–8 use editable inline SVG diagrams: an illustrative dependency graph, evidence packet, feedback loop, OpenRCA architecture comparison, implementation boundary, proposed paired evaluation, and two future-work loops. Edit labels and geometry directly in `index.html`. The service topology is illustrative, not a measured incident. Solid and dashed paths distinguish documented versus proposed work where labeled.
