/**
 * Copies `baseUrl` (default: the current URL) to the clipboard with
 * `param=value` set in its query string. Used for entity deep links; pass an
 * explicit `baseUrl` when the param is only valid on a specific route.
 */
export const copyUrlWithSearchParam = async (
  param: string,
  value: string | number,
  baseUrl: string = window.location.href
) => {
  const url = new URL(baseUrl);
  url.searchParams.set(param, String(value));
  await navigator.clipboard.writeText(url.toString());
};
