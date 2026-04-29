/**
 * Pokémon API → Fivetran → Databricks → dbt → Streamlit
 * Architecture Overview Slide — Google Apps Script
 *
 * Run createArchitectureSlide() from the Apps Script editor to generate
 * the slide in a new Google Presentation.
 *
 * Fivetran brand colours
 *   Primary blue  : #0073E6
 *   Dark navy     : #0A1628
 *   Light blue    : #E6F2FF
 *   Accent green  : #00C49A
 *   Accent orange : #FF6B35
 *   White         : #FFFFFF
 *   Mid-grey      : #8A9BB0
 *   Light grey bg : #F4F7FB
 */

// ─── Colour palette ───────────────────────────────────────────────────────────
const C = {
  navy:        { red: 0.039, green: 0.086, blue: 0.157 },  // #0A1628
  blue:        { red: 0.000, green: 0.451, blue: 0.902 },  // #0073E6
  lightBlue:   { red: 0.902, green: 0.949, blue: 1.000 },  // #E6F2FF
  green:       { red: 0.000, green: 0.769, blue: 0.604 },  // #00C49A
  orange:      { red: 1.000, green: 0.420, blue: 0.208 },  // #FF6B35
  white:       { red: 1.000, green: 1.000, blue: 1.000 },
  midGrey:     { red: 0.541, green: 0.608, blue: 0.690 },  // #8A9BB0
  lightGrey:   { red: 0.957, green: 0.969, blue: 0.984 },  // #F4F7FB
  darkText:    { red: 0.039, green: 0.086, blue: 0.157 },  // same as navy
};

// ─── Slide dimensions (16:9 widescreen in EMU) ───────────────────────────────
const W = 720;   // points (Slides uses pt internally via the API)
const H = 405;

// ─── Entry point ─────────────────────────────────────────────────────────────
function createArchitectureSlide() {
  const pres  = SlidesApp.create("Pokémon Pipeline — Architecture Overview");
  const slide = pres.getSlides()[0];
  slide.getBackground().setSolidFill(rgbObj(C.navy));

  // Remove default placeholder text boxes
  slide.getPageElements().forEach(el => {
    try { el.remove(); } catch (_) {}
  });

  _drawBackground(slide);
  _drawTitle(slide);
  _drawSubtitle(slide);
  _drawPipelineNodes(slide);
  _drawArrows(slide);
  _drawDataLabels(slide);
  _drawFooter(slide);

  Logger.log("Slide created: " + pres.getUrl());
  return pres.getUrl();
}

// ─── Background decoration ───────────────────────────────────────────────────
function _drawBackground(slide) {
  // Subtle grid-dot pattern via a very faint rectangle overlay
  const grad = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 0, W, H);
  grad.getFill().setSolidFill(rgbObj(C.navy));
  grad.getBorder().setTransparent();
  grad.sendToBack();

  // Top accent bar
  const bar = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 0, W, 6);
  bar.getFill().setSolidFill(rgbObj(C.blue));
  bar.getBorder().setTransparent();

  // Bottom accent bar
  const barB = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, H - 4, W, 4);
  barB.getFill().setSolidFill(rgbObj(C.green));
  barB.getBorder().setTransparent();
}

// ─── Title ───────────────────────────────────────────────────────────────────
function _drawTitle(slide) {
  const tb = slide.insertTextBox(
    "Pokémon API  →  Fivetran  →  Databricks  →  dbt  →  Streamlit",
    40, 18, W - 80, 38
  );
  const style = tb.getText().getTextStyle();
  style.setFontFamily("Google Sans").setFontSize(20).setBold(true)
       .setForegroundColor(rgbObj(C.white));
  tb.getText().getParagraphStyle().setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
  tb.getFill().setTransparent();
  tb.getBorder().setTransparent();
}

// ─── Subtitle ────────────────────────────────────────────────────────────────
function _drawSubtitle(slide) {
  const tb = slide.insertTextBox(
    "End-to-end data pipeline: custom connector  ·  Unity Catalog  ·  dbt transformations  ·  live analytics dashboard",
    40, 52, W - 80, 20
  );
  const style = tb.getText().getTextStyle();
  style.setFontFamily("Google Sans").setFontSize(9).setBold(false)
       .setForegroundColor(rgbObj(C.midGrey));
  tb.getText().getParagraphStyle().setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
  tb.getFill().setTransparent();
  tb.getBorder().setTransparent();
}

// ─── Pipeline node definitions ───────────────────────────────────────────────
//  Each node: { id, label, sublabel, icon, x, y, w, h, fillColor, accentColor }
function _pipelineNodes() {
  const nodeH = 100;
  const nodeW = 108;
  const topY  = 105;

  return [
    {
      id: "pokeapi",
      label: "PokéAPI",
      sublabel: "pokeapi.co/api/v2\n8 endpoints\n~1,350 Pokémon",
      icon: "🌐",
      x: 28,   y: topY, w: nodeW, h: nodeH,
      fill: C.navy, accent: C.orange,
      tag: "SOURCE",
    },
    {
      id: "fivetran",
      label: "Fivetran",
      sublabel: "Custom Connector SDK\nIncremental sync\n8 raw tables",
      icon: "⚡",
      x: 164,  y: topY, w: nodeW, h: nodeH,
      fill: C.blue, accent: C.lightBlue,
      tag: "INGEST",
    },
    {
      id: "databricks",
      label: "Databricks",
      sublabel: "Unity Catalog\njason_chletsos\n.pokemon_marts",
      icon: "🧱",
      x: 306,  y: topY, w: nodeW, h: nodeH,
      fill: C.navy, accent: C.green,
      tag: "STORE",
    },
    {
      id: "dbt",
      label: "dbt Core",
      sublabel: "8 staging views\n8 mart tables\nSnowflake → Databricks",
      icon: "🔧",
      x: 448,  y: topY, w: nodeW, h: nodeH,
      fill: C.navy, accent: C.orange,
      tag: "TRANSFORM",
    },
    {
      id: "streamlit",
      label: "Streamlit",
      sublabel: "7 analytics pages\nECS Fargate + ALB\ndatabricks-sql-connector",
      icon: "📊",
      x: 590,  y: topY, w: nodeW, h: nodeH,
      fill: C.navy, accent: C.blue,
      tag: "VISUALISE",
    },
  ];
}

// ─── Draw nodes ──────────────────────────────────────────────────────────────
function _drawPipelineNodes(slide) {
  const nodes = _pipelineNodes();

  nodes.forEach(n => {
    // Card background
    const card = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE,
      n.x, n.y, n.w, n.h);
    card.getFill().setSolidFill(rgbObj({ red: 0.07, green: 0.13, blue: 0.22 }));
    card.getBorder().getLineFill().setSolidFill(rgbObj(n.accent));
    card.getBorder().setWeight(1.5);

    // Accent top strip
    const strip = slide.insertShape(SlidesApp.ShapeType.RECTANGLE,
      n.x, n.y, n.w, 5);
    strip.getFill().setSolidFill(rgbObj(n.accent));
    strip.getBorder().setTransparent();

    // Tag pill
    const pill = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE,
      n.x + 6, n.y + 9, n.w - 12, 14);
    pill.getFill().setSolidFill(rgbObj(n.accent));
    pill.getBorder().setTransparent();
    const pillTb = slide.insertTextBox(n.tag, n.x + 6, n.y + 9, n.w - 12, 14);
    pillTb.getText().getTextStyle()
      .setFontFamily("Google Sans").setFontSize(6).setBold(true)
      .setForegroundColor(rgbObj(C.navy));
    pillTb.getText().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    pillTb.getFill().setTransparent();
    pillTb.getBorder().setTransparent();

    // Icon
    const iconTb = slide.insertTextBox(n.icon, n.x, n.y + 26, n.w, 22);
    iconTb.getText().getTextStyle().setFontSize(18);
    iconTb.getText().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    iconTb.getFill().setTransparent();
    iconTb.getBorder().setTransparent();

    // Label
    const labelTb = slide.insertTextBox(n.label, n.x, n.y + 50, n.w, 16);
    labelTb.getText().getTextStyle()
      .setFontFamily("Google Sans").setFontSize(11).setBold(true)
      .setForegroundColor(rgbObj(C.white));
    labelTb.getText().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    labelTb.getFill().setTransparent();
    labelTb.getBorder().setTransparent();

    // Sublabel
    const subTb = slide.insertTextBox(n.sublabel, n.x + 4, n.y + 66, n.w - 8, 32);
    subTb.getText().getTextStyle()
      .setFontFamily("Google Sans").setFontSize(7)
      .setForegroundColor(rgbObj(C.midGrey));
    subTb.getText().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    subTb.getFill().setTransparent();
    subTb.getBorder().setTransparent();
  });
}

// ─── Arrows between nodes ────────────────────────────────────────────────────
function _drawArrows(slide) {
  const nodes  = _pipelineNodes();
  const arrowY = 105 + 50; // vertical midpoint of cards

  const arrowLabels = [
    "REST\nHTTPS",
    "SDK\nupsert",
    "SQL\nWarehouse",
    "SELECT *\nmaterialize",
  ];

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
    line.getLineFill().setSolidFill(rgbObj(C.blue));
    line.setWeight(1.5);
    line.setEndArrow(SlidesApp.ArrowStyle.FILL_ARROW);

    // Arrow label
    const lbTb = slide.insertTextBox(
      arrowLabels[i], midX - 20, arrowY - 18, 40, 18
    );
    lbTb.getText().getTextStyle()
      .setFontFamily("Google Sans").setFontSize(6.5)
      .setForegroundColor(rgbObj(C.midGrey));
    lbTb.getText().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    lbTb.getFill().setTransparent();
    lbTb.getBorder().setTransparent();
  }
}

// ─── Data flow detail labels (below the pipeline) ────────────────────────────
function _drawDataLabels(slide) {
  const detailY = 222;
  const details = [
    { x: 28,  w: 108, text: "8 API endpoints\npokemon · moves\nspecies · types\nabilities · stats" },
    { x: 164, w: 108, text: "Incremental cursor\nstate-based sync\nFivetran SDK v1\nAuto-schema mgmt" },
    { x: 306, w: 108, text: "Unity Catalog\njason_chletsos\npokemon_marts\n8 Delta tables" },
    { x: 448, w: 108, text: "8 staging views\n8 mart tables\ndim · fct · mart\nSnowflake source" },
    { x: 590, w: 108, text: "Overview · Attackers\nDefenders · Movesets\nLegendary · Types\nPokédex · Stats" },
  ];

  // Section header
  const hdr = slide.insertTextBox("DATA FLOW DETAIL", 28, detailY - 14, W - 56, 12);
  hdr.getText().getTextStyle()
    .setFontFamily("Google Sans").setFontSize(7).setBold(true)
    .setForegroundColor(rgbObj(C.blue));
  hdr.getFill().setTransparent();
  hdr.getBorder().setTransparent();

  // Divider line
  const div = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, 28, detailY, W - 28, detailY);
  div.getLineFill().setSolidFill(rgbObj({ red: 0.1, green: 0.2, blue: 0.35 }));
  div.setWeight(0.75);

  details.forEach(d => {
    const box = slide.insertShape(SlidesApp.ShapeType.RECTANGLE,
      d.x, detailY + 4, d.w, 68);
    box.getFill().setSolidFill(rgbObj({ red: 0.055, green: 0.11, blue: 0.19 }));
    box.getBorder().setTransparent();

    const tb = slide.insertTextBox(d.text, d.x + 4, detailY + 6, d.w - 8, 64);
    tb.getText().getTextStyle()
      .setFontFamily("Google Sans").setFontSize(7.5)
      .setForegroundColor(rgbObj(C.midGrey));
    tb.getText().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    tb.getFill().setTransparent();
    tb.getBorder().setTransparent();
  });
}

// ─── Footer ──────────────────────────────────────────────────────────────────
function _drawFooter(slide) {
  // AWS infra strip
  const infoBg = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 302, W, 26);
  infoBg.getFill().setSolidFill(rgbObj({ red: 0.04, green: 0.09, blue: 0.17 }));
  infoBg.getBorder().setTransparent();

  const awsText = "☁  AWS ECS Fargate  ·  Application Load Balancer  ·  ECR  ·  Secrets Manager  ·  CodeBuild  ·  S3  ·  CloudWatch";
  const awsTb = slide.insertTextBox(awsText, 20, 306, W - 40, 16);
  awsTb.getText().getTextStyle()
    .setFontFamily("Google Sans").setFontSize(7.5)
    .setForegroundColor(rgbObj(C.midGrey));
  awsTb.getText().getParagraphStyle()
    .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
  awsTb.getFill().setTransparent();
  awsTb.getBorder().setTransparent();

  // Live URL badge
  const badge = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, 160, 334, 400, 22);
  badge.getFill().setSolidFill(rgbObj(C.blue));
  badge.getBorder().setTransparent();

  const urlTb = slide.insertTextBox(
    "🔗  pokemon-databricks-alb-1573601121.us-east-1.elb.amazonaws.com",
    160, 336, 400, 18
  );
  urlTb.getText().getTextStyle()
    .setFontFamily("Google Sans").setFontSize(8).setBold(true)
    .setForegroundColor(rgbObj(C.white));
  urlTb.getText().getParagraphStyle()
    .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
  urlTb.getFill().setTransparent();
  urlTb.getBorder().setTransparent();

  // Fivetran wordmark bottom-right
  const ftTb = slide.insertTextBox("Built with Fivetran", W - 120, H - 22, 110, 14);
  ftTb.getText().getTextStyle()
    .setFontFamily("Google Sans").setFontSize(7).setBold(true)
    .setForegroundColor(rgbObj(C.blue));
  ftTb.getText().getParagraphStyle()
    .setParagraphAlignment(SlidesApp.ParagraphAlignment.RIGHT);
  ftTb.getFill().setTransparent();
  ftTb.getBorder().setTransparent();

  // Date bottom-left
  const dateTb = slide.insertTextBox("April 2026", 10, H - 22, 80, 14);
  dateTb.getText().getTextStyle()
    .setFontFamily("Google Sans").setFontSize(7)
    .setForegroundColor(rgbObj(C.midGrey));
  dateTb.getFill().setTransparent();
  dateTb.getBorder().setTransparent();
}

// ─── Utility: convert { red, green, blue } 0-1 floats to a hex string ────────
function rgbObj(c) {
  // Apps Script setSolidFill accepts a hex string "#RRGGBB"
  const toHex = v => Math.round(v * 255).toString(16).padStart(2, "0");
  return "#" + toHex(c.red) + toHex(c.green) + toHex(c.blue);
}
