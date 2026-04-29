/**
 * Pokémon API → Fivetran → Databricks → dbt → Streamlit
 * Architecture Overview Slide — Google Apps Script
 *
 * Run createArchitectureSlide() from the Apps Script editor.
 *
 * Fivetran brand colours
 *   Primary blue  : #0073E6
 *   Dark navy     : #0A1628
 *   Accent green  : #00C49A
 *   Accent orange : #FF6B35
 *   White         : #FFFFFF
 *   Mid-grey      : #8A9BB0
 */

// ─── Colour palette (hex strings — setSolidFill accepts "#RRGGBB") ───────────
const C = {
  navy:      "#0A1628",
  blue:      "#0073E6",
  lightBlue: "#E6F2FF",
  green:     "#00C49A",
  orange:    "#FF6B35",
  white:     "#FFFFFF",
  midGrey:   "#8A9BB0",
  cardBg:    "#111E33",
  detailBg:  "#0E1B2E",
  footerBg:  "#0A1220",
  divider:   "#1A3055",
};

// ─── Slide dimensions (points) ───────────────────────────────────────────────
const W = 720;
const H = 405;

// ─── Utility: set alignment on every paragraph in a TextRange ────────────────
function setAlign(textRange, alignment) {
  textRange.getParagraphs().forEach(p => {
    p.getRange().getParagraphStyle().setParagraphAlignment(alignment);
  });
}

// ─── Entry point ─────────────────────────────────────────────────────────────
function createArchitectureSlide() {
  const pres  = SlidesApp.create("Pokémon Pipeline — Architecture Overview");
  const slide = pres.getSlides()[0];
  slide.getBackground().setSolidFill(C.navy);

  // Remove default placeholder elements
  slide.getPageElements().forEach(el => { try { el.remove(); } catch (_) {} });

  _drawBackground(slide);
  _drawTitle(slide);
  _drawSubtitle(slide);
  _drawPipelineNodes(slide);
  _drawArrows(slide);
  _drawDataLabels(slide);
  _drawFooter(slide);

  Logger.log("✅ Slide created: " + pres.getUrl());
  return pres.getUrl();
}

// ─── Background decoration ───────────────────────────────────────────────────
function _drawBackground(slide) {
  // Top accent bar
  const barT = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 0, W, 6);
  barT.getFill().setSolidFill(C.blue);
  barT.getBorder().setTransparent();

  // Bottom accent bar
  const barB = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, H - 4, W, 4);
  barB.getFill().setSolidFill(C.green);
  barB.getBorder().setTransparent();
}

// ─── Helper: insert a styled text box ────────────────────────────────────────
function _tb(slide, text, x, y, w, h, opts) {
  const box = slide.insertTextBox(text, x, y, w, h);
  const style = box.getText().getTextStyle();
  if (opts.font)      style.setFontFamily(opts.font);
  if (opts.size)      style.setFontSize(opts.size);
  if (opts.bold)      style.setBold(true);
  if (opts.color)     style.setForegroundColor(opts.color);
  if (opts.align)     setAlign(box.getText(), opts.align);
  box.getFill().setTransparent();
  box.getBorder().setTransparent();
  return box;
}

// ─── Title ───────────────────────────────────────────────────────────────────
function _drawTitle(slide) {
  _tb(slide,
    "Pokémon API  →  Fivetran  →  Databricks  →  dbt  →  Streamlit",
    40, 14, W - 80, 36,
    { font: "Google Sans", size: 20, bold: true, color: C.white,
      align: SlidesApp.ParagraphAlignment.CENTER }
  );
}

// ─── Subtitle ────────────────────────────────────────────────────────────────
function _drawSubtitle(slide) {
  _tb(slide,
    "End-to-end data pipeline: custom connector  ·  Unity Catalog  ·  dbt transformations  ·  live analytics dashboard",
    40, 50, W - 80, 18,
    { font: "Google Sans", size: 8.5, color: C.midGrey,
      align: SlidesApp.ParagraphAlignment.CENTER }
  );
}

// ─── Pipeline node definitions ───────────────────────────────────────────────
function _pipelineNodes() {
  const nodeH = 100;
  const nodeW = 108;
  const topY  = 72;

  return [
    {
      label: "PokéAPI",
      sublabel: "pokeapi.co/api/v2\n8 endpoints\n~1,350 Pokémon",
      icon: "🌐",
      x: 28,  y: topY, w: nodeW, h: nodeH,
      accent: C.orange, tag: "SOURCE",
    },
    {
      label: "Fivetran",
      sublabel: "Custom Connector SDK\nIncremental sync\n8 raw tables",
      icon: "⚡",
      x: 164, y: topY, w: nodeW, h: nodeH,
      accent: C.blue, tag: "INGEST",
    },
    {
      label: "Databricks",
      sublabel: "Unity Catalog\njason_chletsos\n.pokemon_marts",
      icon: "🧱",
      x: 306, y: topY, w: nodeW, h: nodeH,
      accent: C.green, tag: "STORE",
    },
    {
      label: "dbt Core",
      sublabel: "8 staging views\n8 mart tables\nSnowflake → Databricks",
      icon: "🔧",
      x: 448, y: topY, w: nodeW, h: nodeH,
      accent: C.orange, tag: "TRANSFORM",
    },
    {
      label: "Streamlit",
      sublabel: "7 analytics pages\nECS Fargate + ALB\ndatabricks-sql-connector",
      icon: "📊",
      x: 590, y: topY, w: nodeW, h: nodeH,
      accent: C.blue, tag: "VISUALISE",
    },
  ];
}

// ─── Draw nodes ──────────────────────────────────────────────────────────────
function _drawPipelineNodes(slide) {
  _pipelineNodes().forEach(n => {
    // Card background
    const card = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE,
      n.x, n.y, n.w, n.h);
    card.getFill().setSolidFill(C.cardBg);
    card.getBorder().getLineFill().setSolidFill(n.accent);
    card.getBorder().setWeight(1.5);

    // Accent top strip
    const strip = slide.insertShape(SlidesApp.ShapeType.RECTANGLE,
      n.x, n.y, n.w, 5);
    strip.getFill().setSolidFill(n.accent);
    strip.getBorder().setTransparent();

    // Tag pill background
    const pill = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE,
      n.x + 6, n.y + 9, n.w - 12, 14);
    pill.getFill().setSolidFill(n.accent);
    pill.getBorder().setTransparent();

    // Tag pill text
    _tb(slide, n.tag, n.x + 6, n.y + 9, n.w - 12, 14,
      { font: "Google Sans", size: 6, bold: true, color: C.navy,
        align: SlidesApp.ParagraphAlignment.CENTER });

    // Icon
    _tb(slide, n.icon, n.x, n.y + 26, n.w, 22,
      { size: 18, align: SlidesApp.ParagraphAlignment.CENTER });

    // Label
    _tb(slide, n.label, n.x, n.y + 50, n.w, 16,
      { font: "Google Sans", size: 11, bold: true, color: C.white,
        align: SlidesApp.ParagraphAlignment.CENTER });

    // Sublabel
    _tb(slide, n.sublabel, n.x + 4, n.y + 67, n.w - 8, 30,
      { font: "Google Sans", size: 7, color: C.midGrey,
        align: SlidesApp.ParagraphAlignment.CENTER });
  });
}

// ─── Arrows between nodes ────────────────────────────────────────────────────
function _drawArrows(slide) {
  const nodes  = _pipelineNodes();
  const arrowY = 72 + 50; // vertical midpoint of cards

  const labels = ["REST\nHTTPS", "SDK\nupsert", "SQL\nWarehouse", "SELECT *\nmaterialize"];

  for (let i = 0; i < nodes.length - 1; i++) {
    const from = nodes[i];
    const to   = nodes[i + 1];
    const x1   = from.x + from.w + 2;
    const x2   = to.x - 2;
    const midX = (x1 + x2) / 2;

    // Arrow line
    const line = slide.insertLine(
      SlidesApp.LineCategory.STRAIGHT,
      x1, arrowY, x2, arrowY
    );
    line.getLineFill().setSolidFill(C.blue);
    line.setWeight(1.5);
    line.setEndArrow(SlidesApp.ArrowStyle.FILL_ARROW);

    // Arrow label
    _tb(slide, labels[i], midX - 20, arrowY - 20, 40, 18,
      { font: "Google Sans", size: 6.5, color: C.midGrey,
        align: SlidesApp.ParagraphAlignment.CENTER });
  }
}

// ─── Data flow detail section ─────────────────────────────────────────────────
function _drawDataLabels(slide) {
  const sectionY = 186;

  // Section header
  _tb(slide, "DATA FLOW DETAIL",
    28, sectionY, W - 56, 12,
    { font: "Google Sans", size: 7, bold: true, color: C.blue });

  // Divider line
  const div = slide.insertLine(
    SlidesApp.LineCategory.STRAIGHT, 28, sectionY + 13, W - 28, sectionY + 13);
  div.getLineFill().setSolidFill(C.divider);
  div.setWeight(0.75);

  const details = [
    { x: 28,  w: 108, text: "8 API endpoints\npokemon · moves\nspecies · types\nabilities · stats" },
    { x: 164, w: 108, text: "Incremental cursor\nstate-based sync\nFivetran SDK v1\nAuto-schema mgmt" },
    { x: 306, w: 108, text: "Unity Catalog\njason_chletsos\npokemon_marts\n8 Delta tables" },
    { x: 448, w: 108, text: "8 staging views\n8 mart tables\ndim · fct · mart\nSnowflake source" },
    { x: 590, w: 108, text: "Overview · Attackers\nDefenders · Movesets\nLegendary · Types\nPokédex · Stats" },
  ];

  details.forEach(d => {
    const box = slide.insertShape(SlidesApp.ShapeType.RECTANGLE,
      d.x, sectionY + 16, d.w, 66);
    box.getFill().setSolidFill(C.detailBg);
    box.getBorder().setTransparent();

    _tb(slide, d.text, d.x + 4, sectionY + 18, d.w - 8, 62,
      { font: "Google Sans", size: 7.5, color: C.midGrey,
        align: SlidesApp.ParagraphAlignment.CENTER });
  });
}

// ─── Footer ──────────────────────────────────────────────────────────────────
function _drawFooter(slide) {
  // AWS infra strip
  const infoBg = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 292, W, 26);
  infoBg.getFill().setSolidFill(C.footerBg);
  infoBg.getBorder().setTransparent();

  _tb(slide,
    "☁  AWS ECS Fargate  ·  Application Load Balancer  ·  ECR  ·  Secrets Manager  ·  CodeBuild  ·  S3  ·  CloudWatch",
    20, 296, W - 40, 16,
    { font: "Google Sans", size: 7.5, color: C.midGrey,
      align: SlidesApp.ParagraphAlignment.CENTER });

  // Live URL badge
  const badge = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, 160, 326, 400, 22);
  badge.getFill().setSolidFill(C.blue);
  badge.getBorder().setTransparent();

  _tb(slide,
    "🔗  pokemon-databricks-alb-1573601121.us-east-1.elb.amazonaws.com",
    160, 328, 400, 18,
    { font: "Google Sans", size: 8, bold: true, color: C.white,
      align: SlidesApp.ParagraphAlignment.CENTER });

  // Fivetran wordmark — bottom right
  _tb(slide, "Built with Fivetran",
    W - 120, H - 20, 110, 14,
    { font: "Google Sans", size: 7, bold: true, color: C.blue,
      align: SlidesApp.ParagraphAlignment.RIGHT });

  // Date — bottom left
  _tb(slide, "April 2026",
    10, H - 20, 80, 14,
    { font: "Google Sans", size: 7, color: C.midGrey });
}
