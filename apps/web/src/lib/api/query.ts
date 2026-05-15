/*
 * Helper functions for transforming or querying backend API data.
 */
export type SortDirection = "asc" | "desc";

// Defines the List Query Meta data shape used by this frontend module.
export type ListQueryMeta = {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  sortBy: string;
  sortDirection: SortDirection;
  warnings: string[];
};

// Defines the Query Param Value data shape used by this frontend module.
type QueryParamValue = string | number | boolean | null | undefined;

// Builds api Path data used by the UI.
export function buildApiPath(
  path: string,
  params: Record<string, QueryParamValue>
) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value == null || value === "") {
      return;
    }

    searchParams.set(key, String(value));
  });

  const queryString = searchParams.toString();
  return queryString ? `${path}?${queryString}` : path;
}

// Converts API data into the frontend format for map List Query Meta.
export function mapListQueryMeta(meta: {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort_by: string;
  sort_direction: SortDirection;
  warnings: string[];
}): ListQueryMeta {
  return {
    page: meta.page,
    pageSize: meta.page_size,
    total: meta.total,
    totalPages: meta.total_pages,
    sortBy: meta.sort_by,
    sortDirection: meta.sort_direction,
    warnings: meta.warnings
  };
}
