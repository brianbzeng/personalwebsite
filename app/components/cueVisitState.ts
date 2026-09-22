/** Kept by the room instance: survives shelf unmounts, resets on page refresh. */
export type CueVisitState = { completed: Set<string>; navigated: boolean };
export function createCueVisitState(): CueVisitState {
  return { completed: new Set<string>(), navigated: false };
}
export function rememberCueVisit(memory: CueVisitState, key: string) {
  memory.completed.add(key);
}
export function learnShelfNavigation(memory: CueVisitState) {
  memory.navigated = true;
}
