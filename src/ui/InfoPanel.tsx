import type { Dispatch } from 'react';
import { displayName, secondaryName, sideLabel } from '../atlas/names';
import { systemInfo } from '../atlas/systems';
import type { Origin, PartRecord } from '../atlas/types';
import type { ViewAction, ViewState } from '../atlas/viewState';
import { STRINGS } from './strings';

const ORIGIN_LABEL: Record<Origin, string> = {
  'laki-laki-asli': STRINGS.originMale,
  'perempuan-asli': STRINGS.originFemale,
  'dipasang-dari-laki-laki': STRINGS.originFitted,
};

interface Props {
  part: PartRecord;
  state: ViewState;
  dispatch: Dispatch<ViewAction>;
  onFocus?(id: string): void;
}

export default function InfoPanel({ part, state, dispatch, onFocus }: Props) {
  const secondary = secondaryName(part.names, state.istilah);
  const side = sideLabel(part.side);
  return (
    <aside className="info-panel" aria-label={STRINGS.partInfo}>
      <button type="button" className="close" aria-label={STRINGS.close} onClick={() => dispatch({ type: 'select', id: null })}>
        ×
      </button>
      <h2>{displayName(part.names, state.istilah)}</h2>
      {secondary && <p className="secondary-name">{secondary}</p>}
      <dl>
        <dt>{STRINGS.system}</dt>
        <dd>{systemInfo(part.system).label}</dd>
        {side && (
          <>
            <dt>{STRINGS.side}</dt>
            <dd>{side}</dd>
          </>
        )}
        <dt>{STRINGS.origin}</dt>
        <dd className={part.origin === 'dipasang-dari-laki-laki' ? 'origin fitted' : 'origin'}>{ORIGIN_LABEL[part.origin]}</dd>
      </dl>
      <div className="actions">
        <button type="button" onClick={() => dispatch({ type: 'isolatePart', id: part.id })}>{STRINGS.isolate}</button>
        <button type="button" onClick={() => dispatch({ type: 'hidePart', id: part.id })}>{STRINGS.hide}</button>
        <button type="button" onClick={() => onFocus?.(part.id)}>{STRINGS.focus}</button>
        <button type="button" onClick={() => dispatch({ type: 'showAll' })}>{STRINGS.showAll}</button>
      </div>
    </aside>
  );
}
