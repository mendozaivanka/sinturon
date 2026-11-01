// Sinturon's vocabulary: the four coffees, their colours and how they are named in GBIF.
export const SPECIES = ["arabica", "robusta", "liberica", "excelsa"] as const;
export type Species = (typeof SPECIES)[number];

export type SpeciesInfo = {
  slug: Species;
  name: string;
  scientific: string;
  gbifKey: number;
  /** CSS colour (a custom property, so it follows light and dark). */
  colour: string;
  /** Fixed light-theme hex, for places a CSS variable can't reach. */
  hex: string;
  /** What USDA PSD reports for it. */
  psd: "arabica" | "robusta" | "other";
  blurb: string;
  naming?: string;
};

export const species: Record<Species, SpeciesInfo> = {
  arabica: {
    slug: "arabica", name: "Arabica", scientific: "Coffea arabica L.", gbifKey: 2895345,
    colour: "var(--sp-arabica)", hex: "#3f6178", psd: "arabica",
    blurb: "Most of the world's coffee. Native to the highlands of south-western Ethiopia and the Boma Plateau of South Sudan.",
  },
  robusta: {
    slug: "robusta", name: "Robusta", scientific: "Coffea canephora Pierre ex A.Froehner", gbifKey: 2895528,
    colour: "var(--sp-robusta)", hex: "#8f3a5c", psd: "robusta",
    blurb: "The lowland coffee, sold as robusta. Native across West and Central Africa's forests.",
    naming: "Robusta is a trade name: GBIF and botanists file it as Coffea canephora.",
  },
  liberica: {
    slug: "liberica", name: "Liberica", scientific: "Coffea liberica W.Bull", gbifKey: 8524134,
    colour: "var(--sp-liberica)", hex: "#5f8f6c", psd: "other",
    blurb: "A large-fruited West African coffee, grown in the Philippines as kapeng barako.",
  },
  excelsa: {
    slug: "excelsa", name: "Excelsa", scientific: "Coffea liberica var. dewevrei (De Wild. & T.Durand) Lebrun", gbifKey: 2895394,
    colour: "var(--sp-excelsa)", hex: "#9c86c9", psd: "other",
    blurb: "Sold as excelsa. Botanists treat it as a variety of liberica from Central Africa.",
    naming: "GBIF files excelsa as Coffea liberica var. dewevrei (its synonym C. dewevrei is merged in).",
  },
};

export const fmt = (n: number) => n.toLocaleString("en-US");
export const pct = (n: number | null | undefined) => (n == null ? "–" : `${n.toFixed(1)}%`);
export const BASIS_LABEL: Record<string, string> = {
  HUMAN_OBSERVATION: "observation",
  PRESERVED_SPECIMEN: "herbarium specimen",
  OCCURRENCE: "occurrence (unspecified)",
  MATERIAL_SAMPLE: "material sample",
  MATERIAL_CITATION: "literature citation",
  MACHINE_OBSERVATION: "machine observation",
  OBSERVATION: "observation",
  LIVING_SPECIMEN: "living plant",
};
