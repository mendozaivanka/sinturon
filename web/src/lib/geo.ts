/**
 * Build-time map geometry: Equal Earth, Natural Earth 110m land (world-atlas), cropped to 76° N – 56° S.
 * Everything is projected here so pages ship plain SVG; the map island only toggles what is drawn.
 */
import { geoEqualEarth, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
import land110 from "world-atlas/land-110m.json";
import type { Cell } from "@/lib/data/schemas";
import { SPECIES, type Species } from "@/lib/sinturon";

export const TROPIC = 23.44;
export const W = 960;
const NORTH = 76, SOUTH = -56;

const projection = geoEqualEarth().fitWidth(W, { type: "Sphere" });
const yOf = (lat: number) => projection([0, lat])![1];
const Y0 = yOf(NORTH), Y1 = yOf(SOUTH);
export const H = Math.round(Y1 - Y0);
// Shift so the crop's top edge is y = 0.
projection.translate([projection.translate()[0], projection.translate()[1] - Y0]);

export const project = (lon: number, lat: number): [number, number] => {
  const [x, y] = projection([lon, lat])!;
  return [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
};

const topo = land110 as unknown as Topology<{ land: GeometryCollection }>;
const landGeo = feature(topo, topo.objects.land);
const round = (d: string) => d.replace(/(\d+\.\d)\d+/g, "$1");
export const landPath = round(geoPath(projection)(landGeo) ?? "");

export const tropics = { north: project(0, TROPIC)[1], south: project(0, -TROPIC)[1] };

export type Dot = { x: number; y: number; r: number; n: number; lat: number; lon: number; first: number | null; last: number | null };

/** One circle per 3° cell; area ∝ records, r = max(2.2, rmax·√(n/max)). `max` is shared so sizes compare. */
export function dots(cells: Record<Species, Cell[]>, opts: { rmax?: number; only?: Species[] } = {}) {
  const rmax = opts.rmax ?? 18;
  const shown = (opts.only ?? [...SPECIES]) as Species[];
  const max = Math.max(1, ...shown.flatMap((s) => cells[s].map((c) => c[2])));
  const out = {} as Record<Species, Dot[]>;
  for (const s of SPECIES) {
    out[s] = shown.includes(s)
      ? cells[s]
          .map(([lat, lon, n, first, last]) => {
            const [x, y] = project(lon, lat);
            return { x, y, r: Math.round(Math.max(2.2, rmax * Math.sqrt(n / max)) * 10) / 10, n, lat, lon, first, last };
          })
          .sort((a, b) => b.n - a.n)
      : [];
  }
  return { dots: out, max };
}

const deg = (v: number, pos: string, neg: string) => `${Math.abs(v).toFixed(1)}° ${v >= 0 ? pos : neg}`;
export const cellLabel = (d: Dot, name: string) =>
  `${name}: ${d.n.toLocaleString("en-US")} record${d.n === 1 ? "" : "s"} in the 3° cell around ${deg(d.lat, "N", "S")}, ${deg(d.lon, "E", "W")}` +
  (d.first ? ` · ${d.first === d.last ? d.first : `${d.first}–${d.last}`}` : "");
