/**
 * What a data source has to provide. Return plain data in the shapes of `../schemas.ts`; the data layer
 * validates it, so a source can be a thin wrapper over files, a database query or an API call.
 */
export interface DataSource {
  /** Shown in build errors, e.g. "local" or "http". */
  name: string;
  sinturon: {
    records(): Promise<unknown>;
    cells(): Promise<unknown>;
    latitude(): Promise<unknown>;
    outliers(): Promise<unknown>;
    production(): Promise<unknown>;
    datasets(): Promise<unknown>;
    summary(): Promise<unknown>;
  };
}
