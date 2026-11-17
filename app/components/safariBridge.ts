export const HUB_CHANNEL = 'bz-hub-v1';
export const HUB_ORIGIN = 'https://gallery.brianbzeng.com';
export const REPORT_URL = `${HUB_ORIGIN}/featured`;
export const HUB_PATHS = ['/', '/index', '/about'] as const;
export type HubPath = typeof HUB_PATHS[number];
export type HubState = { path: HubPath; title: string; canBack: boolean; canForward: boolean };
export function isHubPath(path: unknown): path is HubPath {
  return typeof path === 'string' && (HUB_PATHS as readonly string[]).includes(path);
}
export function hubOriginForPreview(hostname: string, search: string) {
  return ['127.0.0.1', 'localhost'].includes(hostname) && new URLSearchParams(search).get('hubPreview') === 'local'
    ? 'http://127.0.0.1:4178' : HUB_ORIGIN;
}
export function readHubState(data: unknown): HubState | null {
  if (!data || typeof data !== 'object') return null;
  const value = data as Record<string, unknown>;
  if (value.channel !== HUB_CHANNEL || value.type !== 'state' || !isHubPath(value.path) ||
    typeof value.title !== 'string' || value.title.length > 160 ||
    typeof value.canBack !== 'boolean' || typeof value.canForward !== 'boolean') return null;
  return {path: value.path, title: value.title, canBack: value.canBack, canForward: value.canForward};
}
