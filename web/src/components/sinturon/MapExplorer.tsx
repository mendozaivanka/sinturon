import { useMemo, useState, type ReactNode } from "react";
import type { Dot } from "@/lib/geo";
import type { Species } from "@/lib/sinturon";

type Props = {
  /** Pre-projected circles per species (lib/geo.ts `dots`), all sized against one shared maximum. */
  dots: Record<Species, Dot[]>;
  names: Record<Species, string>;
  colours: Record<Species, string>;
  totals: Record<Species, number>;
  width: number;
  height: number;
  /** The server-rendered base map (land, tropics), passed as children. */
  children?: ReactNode;
};

const ORDER: Species[] = ["arabica", "robusta", "liberica", "excelsa"];
const deg = (v: number, pos: string, neg: string) => `${Math.abs(v).toFixed(1)}° ${v >= 0 ? pos : neg}`;

/** Species toggles over the static base map. Only the circles are drawn in the browser. */
export default function MapExplorer({ dots, names, colours, totals, width, height, children }: Props) {
  const [on, setOn] = useState<Record<Species, boolean>>({ arabica: true, robusta: true, liberica: true, excelsa: true });
  const [hover, setHover] = useState<{ s: Species; d: Dot } | null>(null);
  const shown = ORDER.filter((s) => on[s]);
  const count = useMemo(() => shown.reduce((a, s) => a + totals[s], 0), [shown.join(), totals]);

  return (
    <div className="grid gap-3">
      <div role="group" aria-label="Species shown on the map" className="flex flex-wrap gap-2">
        {ORDER.map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={on[s]}
            onClick={() => setOn((o) => ({ ...o, [s]: !o[s] }))}
            className="inline-flex min-h-11 items-center gap-2 rounded-full border border-border bg-card px-4 text-sm font-medium text-muted-foreground transition-colors aria-pressed:text-foreground aria-pressed:shadow-sm"
            style={on[s] ? { borderColor: colours[s] } : undefined}
          >
            <span
              aria-hidden="true"
              className="inline-block size-3 rounded-full border"
              style={{ borderColor: colours[s], background: on[s] ? `color-mix(in srgb, ${colours[s]} 35%, transparent)` : "transparent" }}
            />
            {names[s]} <span className="font-mono text-xs">{totals[s].toLocaleString("en-US")}</span>
          </button>
        ))}
      </div>
      <div className="relative">
        {children}
        <svg viewBox={`0 0 ${width} ${height}`} className="absolute inset-0 h-full w-full" aria-hidden="true">
          {shown.map((s) => (
            <g key={s} fill={colours[s]} fillOpacity={0.35} stroke={colours[s]} strokeWidth={1}>
              {dots[s].map((d) => (
                <circle
                  key={`${d.lat},${d.lon}`}
                  cx={d.x}
                  cy={d.y}
                  r={d.r}
                  onPointerEnter={() => setHover({ s, d })}
                  onPointerLeave={() => setHover((h) => (h?.d === d ? null : h))}
                />
              ))}
            </g>
          ))}
          {hover && <circle cx={hover.d.x} cy={hover.d.y} r={hover.d.r + 2} fill="none" stroke="var(--foreground)" strokeWidth={1.5} />}
        </svg>
      </div>
      <p className="min-h-6 font-mono text-xs text-muted-foreground" aria-live="polite">
        {hover
          ? `${names[hover.s]}: ${hover.d.n.toLocaleString("en-US")} record${hover.d.n === 1 ? "" : "s"} in the 3° cell around ${deg(hover.d.lat, "N", "S")}, ${deg(hover.d.lon, "E", "W")}${hover.d.first ? ` · ${hover.d.first === hover.d.last ? hover.d.first : `${hover.d.first}–${hover.d.last}`}` : ""}`
          : `${count.toLocaleString("en-US")} records shown. Point at a circle for its count.`}
      </p>
    </div>
  );
}
