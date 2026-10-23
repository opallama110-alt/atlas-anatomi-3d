import { useState, type Dispatch } from 'react';
import { LAYER_GROUPS, SYSTEMS } from '../atlas/systems';
import type { ViewAction, ViewState } from '../atlas/viewState';
import { STRINGS } from './strings';

interface Props {
  state: ViewState;
  dispatch: Dispatch<ViewAction>;
}

export default function LayerBar({ state, dispatch }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <nav className="layer-bar" aria-label={STRINGS.layers}>
      {open && (
        <div className="system-list" role="group" aria-label={STRINGS.allSystems}>
          {SYSTEMS.map((system) => (
            <label key={system.id}>
              <input
                type="checkbox"
                checked={state.systems[system.id]}
                onChange={() => dispatch({ type: 'toggleSystem', system: system.id })}
              />
              <span className="swatch" style={{ background: system.color }} aria-hidden="true" />
              {system.label}
            </label>
          ))}
        </div>
      )}
      <div className="layer-groups">
        {LAYER_GROUPS.map((group) => {
          const on = group.systems.every((s) => state.systems[s]);
          const partial = !on && group.systems.some((s) => state.systems[s]);
          return (
            <button
              key={group.id}
              type="button"
              className={on ? 'chip on' : partial ? 'chip partial' : 'chip'}
              aria-pressed={on}
              onClick={() => dispatch({ type: 'setGroup', group: group.id, on: !on })}
            >
              {group.label}
            </button>
          );
        })}
        <button type="button" className="chip more" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          {STRINGS.allSystems}
        </button>
      </div>
    </nav>
  );
}
