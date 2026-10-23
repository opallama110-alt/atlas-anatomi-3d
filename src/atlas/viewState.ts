import { LAYER_GROUPS, SYSTEMS } from './systems';
import type { BodyId, Istilah, LayerGroupId, SystemId } from './types';

export interface ViewState {
  body: BodyId;
  istilah: Istilah;
  systems: Record<SystemId, boolean>;
  xray: boolean;
  explode: number;
  selectedId: string | null;
  hiddenIds: string[];
  isolatedIds: string[] | null;
}

export type ViewAction =
  | { type: 'setBody'; body: BodyId }
  | { type: 'setIstilah'; istilah: Istilah }
  | { type: 'toggleSystem'; system: SystemId }
  | { type: 'setGroup'; group: LayerGroupId; on: boolean }
  | { type: 'setXray'; on: boolean }
  | { type: 'setExplode'; amount: number }
  | { type: 'select'; id: string | null }
  | { type: 'hidePart'; id: string }
  | { type: 'isolatePart'; id: string }
  | { type: 'showAll' }
  | { type: 'revealPart'; id: string; system: SystemId };

export function initialViewState(body: BodyId = 'male'): ViewState {
  const systems = Object.fromEntries(SYSTEMS.map((s) => [s.id, s.initial])) as Record<SystemId, boolean>;
  return { body, istilah: 'ringan', systems, xray: true, explode: 0, selectedId: null, hiddenIds: [], isolatedIds: null };
}

export function viewReducer(state: ViewState, action: ViewAction): ViewState {
  switch (action.type) {
    case 'setBody':
      return { ...state, body: action.body, selectedId: null, hiddenIds: [], isolatedIds: null };
    case 'setIstilah':
      return { ...state, istilah: action.istilah };
    case 'toggleSystem':
      return { ...state, systems: { ...state.systems, [action.system]: !state.systems[action.system] } };
    case 'setGroup': {
      const group = LAYER_GROUPS.find((g) => g.id === action.group);
      if (!group) return state;
      const systems = { ...state.systems };
      for (const id of group.systems) systems[id] = action.on;
      return { ...state, systems };
    }
    case 'setXray':
      return { ...state, xray: action.on };
    case 'setExplode':
      return { ...state, explode: Math.min(1, Math.max(0, action.amount)) };
    case 'select':
      return { ...state, selectedId: action.id };
    case 'hidePart':
      return {
        ...state,
        hiddenIds: state.hiddenIds.includes(action.id) ? state.hiddenIds : [...state.hiddenIds, action.id],
        selectedId: state.selectedId === action.id ? null : state.selectedId,
      };
    case 'isolatePart':
      return { ...state, isolatedIds: [action.id], selectedId: action.id };
    case 'showAll':
      return { ...state, hiddenIds: [], isolatedIds: null };
    case 'revealPart':
      return {
        ...state,
        systems: { ...state.systems, [action.system]: true },
        hiddenIds: state.hiddenIds.filter((id) => id !== action.id),
        isolatedIds: state.isolatedIds && !state.isolatedIds.includes(action.id) ? null : state.isolatedIds,
        selectedId: action.id,
      };
  }
}

export function isPartVisible(state: ViewState, part: { id: string; system: SystemId }): boolean {
  return (
    state.systems[part.system] &&
    !state.hiddenIds.includes(part.id) &&
    (state.isolatedIds === null || state.isolatedIds.includes(part.id))
  );
}
