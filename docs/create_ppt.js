const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaVideo, FaSearch, FaCogs, FaDatabase, FaCloud, FaRobot,
  FaDocker, FaGithub, FaCheckCircle, FaLightbulb, FaRocket,
  FaUpload, FaCut, FaBrain, FaVectorSquare, FaComments,
  FaChartBar, FaCode, FaShieldAlt, FaClock, FaTwitter
} = require("react-icons/fa");

function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ─── Color Palette: Midnight Executive ───
const BG_DARK    = "0F1729";
const BG_CARD    = "1A2744";
const PRIMARY    = "3B82F6";  // bright blue
const ACCENT     = "60A5FA";  // light blue
const TEXT_WHITE = "FFFFFF";
const TEXT_MUTED = "94A3B8";
const TEXT_LIGHT = "CBD5E1";
const HIGHLIGHT  = "22D3EE";  // cyan accent

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.3 });

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Debraj";
  pres.title = "Video Moments RAG System";

  // ─── Preload icons ───
  const icons = {
    video:    await iconToBase64Png(FaVideo, "#" + HIGHLIGHT),
    search:   await iconToBase64Png(FaSearch, "#" + PRIMARY),
    cogs:     await iconToBase64Png(FaCogs, "#" + ACCENT),
    database: await iconToBase64Png(FaDatabase, "#" + PRIMARY),
    cloud:    await iconToBase64Png(FaCloud, "#" + ACCENT),
    robot:    await iconToBase64Png(FaRobot, "#" + HIGHLIGHT),
    docker:   await iconToBase64Png(FaDocker, "#" + PRIMARY),
    github:   await iconToBase64Png(FaGithub, "#" + TEXT_WHITE),
    check:    await iconToBase64Png(FaCheckCircle, "#22C55E"),
    bulb:     await iconToBase64Png(FaLightbulb, "#FBBF24"),
    rocket:   await iconToBase64Png(FaRocket, "#" + HIGHLIGHT),
    upload:   await iconToBase64Png(FaUpload, "#" + ACCENT),
    cut:      await iconToBase64Png(FaCut, "#" + ACCENT),
    brain:    await iconToBase64Png(FaBrain, "#" + HIGHLIGHT),
    vector:   await iconToBase64Png(FaVectorSquare, "#" + PRIMARY),
    comments: await iconToBase64Png(FaComments, "#" + ACCENT),
    chart:    await iconToBase64Png(FaChartBar, "#" + PRIMARY),
    code:     await iconToBase64Png(FaCode, "#" + ACCENT),
    shield:   await iconToBase64Png(FaShieldAlt, "#22C55E"),
    clock:    await iconToBase64Png(FaClock, "#" + ACCENT),
    twitter:  await iconToBase64Png(FaTwitter, "#" + HIGHLIGHT),
  };

  // ═══════════════════════════════════════
  // SLIDE 1: Title
  // ═══════════════════════════════════════
  let slide = pres.addSlide();
  slide.background = { color: BG_DARK };

  // Accent bar at top
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  // Video icon
  slide.addImage({ data: icons.video, x: 4.5, y: 0.8, w: 1, h: 1 });

  // Title
  slide.addText("Video Moments RAG System", {
    x: 0.5, y: 2.0, w: 9, h: 1,
    fontSize: 40, fontFace: "Calibri", bold: true,
    color: TEXT_WHITE, align: "center", margin: 0
  });

  // Subtitle
  slide.addText("Gemini  +  BigQuery  +  Google ADK", {
    x: 0.5, y: 3.0, w: 9, h: 0.6,
    fontSize: 20, fontFace: "Calibri",
    color: ACCENT, align: "center", charSpacing: 2
  });

  // Author
  slide.addText("Debraj", {
    x: 0.5, y: 4.2, w: 9, h: 0.5,
    fontSize: 16, fontFace: "Calibri",
    color: TEXT_MUTED, align: "center"
  });

  // Bottom bar
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.565, w: 10, h: 0.06, fill: { color: PRIMARY } });


  // ═══════════════════════════════════════
  // SLIDE 2: Problem Statement
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("The Problem", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  // Left column - problem
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.3, h: 3.5,
    fill: { color: BG_CARD }, shadow: makeShadow()
  });
  slide.addImage({ data: icons.search, x: 2.15, y: 1.6, w: 0.7, h: 0.7 });
  slide.addText("Videos Are Not Searchable", {
    x: 0.8, y: 2.4, w: 3.7, h: 0.5,
    fontSize: 18, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", margin: 0
  });
  slide.addText([
    { text: "Hours of content, no way to find specific moments", options: { bullet: true, breakLine: true, color: TEXT_LIGHT } },
    { text: "Manual scrubbing is slow and unreliable", options: { bullet: true, breakLine: true, color: TEXT_LIGHT } },
    { text: "Metadata is sparse — titles and tags aren't enough", options: { bullet: true, color: TEXT_LIGHT } }
  ], { x: 0.9, y: 3.0, w: 3.6, h: 1.5, fontSize: 13, fontFace: "Calibri" });

  // Right column - solution
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.3, h: 3.5,
    fill: { color: BG_CARD }, shadow: makeShadow()
  });
  slide.addImage({ data: icons.robot, x: 6.85, y: 1.6, w: 0.7, h: 0.7 });
  slide.addText("Our Solution", {
    x: 5.5, y: 2.4, w: 3.7, h: 0.5,
    fontSize: 18, fontFace: "Calibri", bold: true, color: HIGHLIGHT, align: "center", margin: 0
  });
  slide.addText([
    { text: "AI extracts structured \"moments\" from video", options: { bullet: true, breakLine: true, color: TEXT_LIGHT } },
    { text: "Vector search enables natural language queries", options: { bullet: true, breakLine: true, color: TEXT_LIGHT } },
    { text: "Ask: \"find the funniest scene\" and get instant results", options: { bullet: true, color: TEXT_LIGHT } }
  ], { x: 5.3, y: 3.0, w: 3.8, h: 1.5, fontSize: 13, fontFace: "Calibri" });


  // ═══════════════════════════════════════
  // SLIDE 3: Architecture
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Architecture", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  // Pipeline boxes
  const pipelineItems = [
    { icon: icons.video,    label: "Video",           sub: "Input",            x: 0.3 },
    { icon: icons.cloud,    label: "GCS",             sub: "Storage",          x: 2.0 },
    { icon: icons.brain,    label: "Gemini 2.5 Pro",  sub: "Extraction",       x: 3.7 },
    { icon: icons.vector,   label: "Embeddings",      sub: "text-embedding-005", x: 5.4 },
    { icon: icons.database, label: "BigQuery",        sub: "VECTOR_SEARCH",    x: 7.1 },
    { icon: icons.robot,    label: "ADK Agent",       sub: "RAG Query",        x: 8.8 },
  ];

  pipelineItems.forEach((item, i) => {
    const y = 1.5;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: item.x, y: y, w: 1.5, h: 2.0,
      fill: { color: BG_CARD }, shadow: makeShadow()
    });
    slide.addImage({ data: item.icon, x: item.x + 0.5, y: y + 0.2, w: 0.5, h: 0.5 });
    slide.addText(item.label, {
      x: item.x + 0.05, y: y + 0.85, w: 1.4, h: 0.45,
      fontSize: 12, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", margin: 0
    });
    slide.addText(item.sub, {
      x: item.x + 0.05, y: y + 1.3, w: 1.4, h: 0.4,
      fontSize: 10, fontFace: "Calibri", color: TEXT_MUTED, align: "center", margin: 0
    });

    // Arrow between boxes
    if (i < pipelineItems.length - 1) {
      const nextX = pipelineItems[i + 1].x;
      const arrowX = item.x + 1.5;
      const arrowW = nextX - arrowX;
      slide.addText("→", {
        x: arrowX, y: y + 0.6, w: arrowW, h: 0.5,
        fontSize: 20, color: ACCENT, align: "center", fontFace: "Calibri", margin: 0
      });
    }
  });

  // Bottom description
  slide.addText("End-to-end pipeline: video segments are analyzed by Gemini, embedded as vectors, stored in BigQuery, and queried through an intelligent agent.", {
    x: 0.7, y: 4.0, w: 8.6, h: 0.8,
    fontSize: 13, fontFace: "Calibri", color: TEXT_MUTED, align: "center"
  });


  // ═══════════════════════════════════════
  // SLIDE 4: Tech Stack
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Tech Stack", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const techItems = [
    ["Python 3.11+",          "Language"],
    ["Gemini 2.5 Pro",        "AI Model (Vertex AI)"],
    ["text-embedding-005",    "Embeddings (768-dim)"],
    ["BigQuery VECTOR_SEARCH","Vector Store (cosine)"],
    ["Google Cloud Storage",  "Object Storage"],
    ["Google ADK",            "Agent Framework"],
    ["ffmpeg",                "Video Processing"],
    ["GitHub Actions",        "CI/CD"],
    ["Docker",                "Containerization"],
    ["Cloud Run",             "Deployment"],
  ];

  // Table header
  slide.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 1.15, w: 7, h: 0.45, fill: { color: PRIMARY } });
  slide.addText("Technology", { x: 1.5, y: 1.15, w: 3.5, h: 0.45, fontSize: 14, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", margin: 0 });
  slide.addText("Purpose", { x: 5.0, y: 1.15, w: 3.5, h: 0.45, fontSize: 14, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", margin: 0 });

  techItems.forEach((item, i) => {
    const y = 1.6 + i * 0.38;
    const bgColor = i % 2 === 0 ? BG_CARD : BG_DARK;
    slide.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: y, w: 7, h: 0.38, fill: { color: bgColor } });
    slide.addText(item[0], { x: 1.7, y: y, w: 3.1, h: 0.38, fontSize: 13, fontFace: "Calibri", bold: true, color: ACCENT, margin: 0, valign: "middle" });
    slide.addText(item[1], { x: 5.2, y: y, w: 3.1, h: 0.38, fontSize: 13, fontFace: "Calibri", color: TEXT_LIGHT, margin: 0, valign: "middle" });
  });


  // ═══════════════════════════════════════
  // SLIDE 5: Ingestion Pipeline
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("How It Works: Ingestion", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const ingestSteps = [
    { icon: icons.upload, num: "1", title: "Upload", desc: "Video uploaded to Google Cloud Storage" },
    { icon: icons.cut,    num: "2", title: "Segment", desc: "ffmpeg splits into ≤10-min chunks" },
    { icon: icons.brain,  num: "3", title: "Extract", desc: "Gemini extracts structured moments (title, entities, mood, timestamps)" },
    { icon: icons.vector, num: "4", title: "Embed", desc: "Moments converted to 768-dim vectors via text-embedding-005" },
    { icon: icons.database, num: "5", title: "Store", desc: "Stored in BigQuery with vector embeddings for search" },
  ];

  ingestSteps.forEach((step, i) => {
    const y = 1.2 + i * 0.82;
    // Number circle
    slide.addShape(pres.shapes.OVAL, { x: 0.8, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: PRIMARY } });
    slide.addText(step.num, { x: 0.8, y: y + 0.05, w: 0.5, h: 0.5, fontSize: 16, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", valign: "middle", margin: 0 });
    // Icon
    slide.addImage({ data: step.icon, x: 1.5, y: y + 0.05, w: 0.45, h: 0.45 });
    // Title
    slide.addText(step.title, { x: 2.15, y: y, w: 1.5, h: 0.55, fontSize: 16, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0, valign: "middle" });
    // Description
    slide.addText(step.desc, { x: 3.6, y: y, w: 5.5, h: 0.55, fontSize: 13, fontFace: "Calibri", color: TEXT_LIGHT, margin: 0, valign: "middle" });

    // Connector line
    if (i < ingestSteps.length - 1) {
      slide.addShape(pres.shapes.LINE, { x: 1.05, y: y + 0.55, w: 0, h: 0.27, line: { color: PRIMARY, width: 2 } });
    }
  });


  // ═══════════════════════════════════════
  // SLIDE 6: RAG Query Flow
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("How It Works: RAG Query", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const querySteps = [
    { icon: icons.comments, num: "1", title: "Ask", desc: "User asks a natural language question" },
    { icon: icons.vector,   num: "2", title: "Embed", desc: "Query embedded with text-embedding-005" },
    { icon: icons.search,   num: "3", title: "Search", desc: "BigQuery VECTOR_SEARCH finds top-k moments (cosine distance)" },
    { icon: icons.robot,    num: "4", title: "Format", desc: "ADK agent formats results with timestamps and clip URLs" },
    { icon: icons.check,    num: "5", title: "Answer", desc: "User gets cited, grounded answers with playable clips" },
  ];

  querySteps.forEach((step, i) => {
    const y = 1.2 + i * 0.82;
    slide.addShape(pres.shapes.OVAL, { x: 0.8, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: HIGHLIGHT.replace("#", "") } });
    slide.addText(step.num, { x: 0.8, y: y + 0.05, w: 0.5, h: 0.5, fontSize: 16, fontFace: "Calibri", bold: true, color: BG_DARK, align: "center", valign: "middle", margin: 0 });
    slide.addImage({ data: step.icon, x: 1.5, y: y + 0.05, w: 0.45, h: 0.45 });
    slide.addText(step.title, { x: 2.15, y: y, w: 1.5, h: 0.55, fontSize: 16, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0, valign: "middle" });
    slide.addText(step.desc, { x: 3.6, y: y, w: 5.5, h: 0.55, fontSize: 13, fontFace: "Calibri", color: TEXT_LIGHT, margin: 0, valign: "middle" });
    if (i < querySteps.length - 1) {
      slide.addShape(pres.shapes.LINE, { x: 1.05, y: y + 0.55, w: 0, h: 0.27, line: { color: HIGHLIGHT, width: 2 } });
    }
  });


  // ═══════════════════════════════════════
  // SLIDE 7: Demo Results
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Demo: Big Bang Theory Clip", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  slide.addText("29-second clip  →  3 moments extracted", {
    x: 0.7, y: 0.9, w: 8.6, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: ACCENT, align: "center", margin: 0
  });

  const moments = [
    { time: "00:00 – 00:07", title: "Penny is Impressed by the Whiteboard", mood: "comedic" },
    { time: "00:07 – 00:15", title: "Sheldon Dismisses Leonard's Work", mood: "comedic" },
    { time: "00:15 – 00:29", title: "Leonard and Sheldon Argue About Physics", mood: "comedic" },
  ];

  moments.forEach((m, i) => {
    const y = 1.5 + i * 0.7;
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: y, w: 8.6, h: 0.6, fill: { color: BG_CARD }, shadow: makeShadow() });
    // Accent bar
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: y, w: 0.06, h: 0.6, fill: { color: PRIMARY } });
    slide.addText(`${i + 1}`, { x: 0.9, y: y, w: 0.4, h: 0.6, fontSize: 16, fontFace: "Calibri", bold: true, color: PRIMARY, valign: "middle", margin: 0 });
    slide.addText(m.title, { x: 1.4, y: y, w: 5.0, h: 0.6, fontSize: 14, fontFace: "Calibri", bold: true, color: TEXT_WHITE, valign: "middle", margin: 0 });
    slide.addText(m.time, { x: 6.5, y: y, w: 1.8, h: 0.6, fontSize: 12, fontFace: "Consolas", color: ACCENT, valign: "middle", align: "center", margin: 0 });
    slide.addText(m.mood, { x: 8.4, y: y, w: 0.8, h: 0.6, fontSize: 11, fontFace: "Calibri", color: TEXT_MUTED, valign: "middle", align: "center", margin: 0 });
  });

  // Query examples
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 3.8, w: 4.1, h: 1.3, fill: { color: BG_CARD }, shadow: makeShadow() });
  slide.addText("Query 1", { x: 0.9, y: 3.9, w: 3.7, h: 0.3, fontSize: 11, fontFace: "Calibri", bold: true, color: ACCENT, margin: 0 });
  slide.addText("\"find funny moments in big_bang_theory\"", { x: 0.9, y: 4.2, w: 3.7, h: 0.3, fontSize: 12, fontFace: "Consolas", color: TEXT_WHITE, margin: 0 });
  slide.addText("→ Returned all 3 moments with timestamps", { x: 0.9, y: 4.5, w: 3.7, h: 0.3, fontSize: 11, fontFace: "Calibri", color: TEXT_MUTED, margin: 0 });

  slide.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 3.8, w: 4.1, h: 1.3, fill: { color: BG_CARD }, shadow: makeShadow() });
  slide.addText("Query 2", { x: 5.4, y: 3.9, w: 3.7, h: 0.3, fontSize: 11, fontFace: "Calibri", bold: true, color: ACCENT, margin: 0 });
  slide.addText("\"who is with the board?\"", { x: 5.4, y: 4.2, w: 3.7, h: 0.3, fontSize: 12, fontFace: "Consolas", color: TEXT_WHITE, margin: 0 });
  slide.addText("→ \"Leonard, Penny, and Sheldon\"", { x: 5.4, y: 4.5, w: 3.7, h: 0.3, fontSize: 11, fontFace: "Calibri", color: TEXT_MUTED, margin: 0 });


  // ═══════════════════════════════════════
  // SLIDE 8: CI/CD Pipeline
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("CI/CD Pipeline", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const cicdItems = [
    { title: "CI — Lint & Test", trigger: "Every Pull Request", color: "22C55E",
      items: ["ruff lint + format check", "pytest (15 unit tests)", "Critical import verification", "Mocked GCP — fast & free"] },
    { title: "CD — Build & Stage", trigger: "Merge to Main", color: PRIMARY,
      items: ["Docker image build", "Push to Artifact Registry", "Staging smoke test", "BQ + GCS + Embedding checks"] },
    { title: "Deploy — Production", trigger: "Manual Trigger", color: "F59E0B",
      items: ["Cloud Run deployment", "Optional BQ table setup", "Post-deploy smoke test", "Traffic routing control"] },
  ];

  cicdItems.forEach((item, i) => {
    const x = 0.5 + i * 3.1;
    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: 1.2, w: 2.9, h: 3.8, fill: { color: BG_CARD }, shadow: makeShadow() });
    // Color accent top
    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: 1.2, w: 2.9, h: 0.06, fill: { color: item.color } });
    slide.addText(item.title, { x: x + 0.15, y: 1.45, w: 2.6, h: 0.5, fontSize: 16, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", margin: 0 });
    // Trigger badge
    slide.addShape(pres.shapes.RECTANGLE, { x: x + 0.35, y: 2.05, w: 2.2, h: 0.35, fill: { color: item.color + "33" } });
    slide.addText(item.trigger, { x: x + 0.35, y: 2.05, w: 2.2, h: 0.35, fontSize: 11, fontFace: "Calibri", color: item.color, align: "center", margin: 0 });

    item.items.forEach((text, j) => {
      slide.addText(text, {
        x: x + 0.3, y: 2.65 + j * 0.5, w: 2.4, h: 0.4,
        fontSize: 12, fontFace: "Calibri", color: TEXT_LIGHT, bullet: true, margin: 0
      });
    });
  });


  // ═══════════════════════════════════════
  // SLIDE 9: Design Decisions
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Design Decisions", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const decisions = [
    { icon: icons.database, title: "BigQuery over Vertex AI Vector Search", desc: "Serverless, no idle cost, pay-per-query. Trade-off: ~2s queries vs <100ms." },
    { icon: icons.code,     title: "Structured Output via response_schema", desc: "Consistent JSON from Gemini, no post-processing or parsing needed." },
    { icon: icons.shield,   title: "Mocked Unit Tests", desc: "Test logic, not APIs. Fast, free, runs anywhere including CI." },
    { icon: icons.clock,    title: "Segment Timestamp Offsetting", desc: "Chunk-relative timestamps shifted back to absolute video time." },
  ];

  decisions.forEach((d, i) => {
    const y = 1.2 + i * 1.05;
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: y, w: 8.6, h: 0.9, fill: { color: BG_CARD }, shadow: makeShadow() });
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: y, w: 0.06, h: 0.9, fill: { color: PRIMARY } });
    slide.addImage({ data: d.icon, x: 1.0, y: y + 0.2, w: 0.45, h: 0.45 });
    slide.addText(d.title, { x: 1.7, y: y + 0.05, w: 7.3, h: 0.4, fontSize: 15, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0 });
    slide.addText(d.desc, { x: 1.7, y: y + 0.45, w: 7.3, h: 0.35, fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED, margin: 0 });
  });


  // ═══════════════════════════════════════
  // SLIDE 10: Key Learnings
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Key Learnings (LLMOps)", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const learnings = [
    { icon: icons.chart,    text: "RAG Pipeline Design" },
    { icon: icons.brain,    text: "Prompt Engineering with Structured Output" },
    { icon: icons.database, text: "Vector Search (BigQuery VECTOR_SEARCH)" },
    { icon: icons.robot,    text: "Agent Orchestration (Google ADK)" },
    { icon: icons.cogs,     text: "CI/CD for LLM Applications" },
    { icon: icons.cloud,    text: "GCP (Vertex AI, BigQuery, GCS, Cloud Run)" },
  ];

  learnings.forEach((l, i) => {
    const col = i < 3 ? 0 : 1;
    const row = i % 3;
    const x = 0.7 + col * 4.5;
    const y = 1.3 + row * 1.25;

    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 4.1, h: 1.0, fill: { color: BG_CARD }, shadow: makeShadow() });
    slide.addImage({ data: l.icon, x: x + 0.25, y: y + 0.25, w: 0.5, h: 0.5 });
    slide.addText(l.text, { x: x + 0.95, y: y, w: 2.9, h: 1.0, fontSize: 14, fontFace: "Calibri", bold: true, color: TEXT_WHITE, valign: "middle", margin: 0 });
  });


  // ═══════════════════════════════════════
  // SLIDE 11: Future Enhancements
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Future Enhancements", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 32, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0
  });

  const futureItems = [
    { icon: icons.twitter,  title: "Social Media Signals", desc: "YouTube/Reddit buzz for ranking boost" },
    { icon: icons.code,     title: "LangChain Alternative", desc: "Portable agent with swappable LLMs" },
    { icon: icons.chart,    title: "LLM Observability", desc: "Latency, token usage, and cost tracking" },
    { icon: icons.cogs,     title: "Prompt Versioning", desc: "A/B testing different prompt strategies" },
    { icon: icons.database, title: "Multi-Source RAG", desc: "Video + social + reviews in one search" },
    { icon: icons.shield,   title: "Evaluation Framework", desc: "Automated quality scoring of LLM outputs" },
  ];

  futureItems.forEach((item, i) => {
    const col = i < 3 ? 0 : 1;
    const row = i % 3;
    const x = 0.7 + col * 4.5;
    const y = 1.3 + row * 1.25;

    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 4.1, h: 1.0, fill: { color: BG_CARD }, shadow: makeShadow() });
    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 0.06, h: 1.0, fill: { color: HIGHLIGHT } });
    slide.addImage({ data: item.icon, x: x + 0.25, y: y + 0.15, w: 0.4, h: 0.4 });
    slide.addText(item.title, { x: x + 0.8, y: y + 0.05, w: 3.0, h: 0.45, fontSize: 14, fontFace: "Calibri", bold: true, color: TEXT_WHITE, margin: 0 });
    slide.addText(item.desc, { x: x + 0.8, y: y + 0.5, w: 3.0, h: 0.35, fontSize: 12, fontFace: "Calibri", color: TEXT_MUTED, margin: 0 });
  });


  // ═══════════════════════════════════════
  // SLIDE 12: Thank You
  // ═══════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: BG_DARK };
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: PRIMARY } });

  slide.addText("Thank You", {
    x: 0.5, y: 1.5, w: 9, h: 1,
    fontSize: 44, fontFace: "Calibri", bold: true, color: TEXT_WHITE, align: "center", margin: 0
  });

  slide.addImage({ data: icons.github, x: 3.5, y: 2.8, w: 0.5, h: 0.5 });
  slide.addText("github.com/debrajaiwork-wq/video-moments-rag", {
    x: 0.5, y: 3.4, w: 9, h: 0.5,
    fontSize: 16, fontFace: "Consolas", color: ACCENT, align: "center",
    hyperlink: { url: "https://github.com/debrajaiwork-wq/video-moments-rag" }
  });

  slide.addText("Debraj", {
    x: 0.5, y: 4.2, w: 9, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: TEXT_MUTED, align: "center"
  });

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.565, w: 10, h: 0.06, fill: { color: PRIMARY } });


  // ─── Write file ───
  const outputPath = "D:\\\\video_moments_rag\\\\docs\\\\Video_Moments_RAG.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log("Presentation saved to: " + outputPath);
}

main().catch(console.error);
