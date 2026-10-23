import type { Dispatch, ReactNode } from 'react';
import type { ViewAction, ViewState } from '../atlas/viewState';
import { STRINGS } from './strings';

interface Props {
  state: ViewState;
  dispatch: Dispatch<ViewAction>;
  search: ReactNode;
}

export default function TopBar({ state, dispatch, search }: Props) {
  return (
    <div className="top-controls">
      <div className="segmented" role="group" aria-label="Badan">
        <button type="button" disabled title={STRINGS.femaleSoon} aria-pressed={state.body === 'female'}>
          {STRINGS.bodyFemale}
        </button>
        <button type="button" aria-pressed={state.body === 'male'} onClick={() => dispatch({ type: 'setBody', body: 'male' })}>
          {STRINGS.bodyMale}
        </button>
      </div>
      <div className="segmented" role="group" aria-label={STRINGS.istilah}>
        <span className="segmented-label">{STRINGS.istilah}</span>
        <button type="button" aria-pressed={state.istilah === 'ringan'} onClick={() => dispatch({ type: 'setIstilah', istilah: 'ringan' })}>
          {STRINGS.istilahRingan}
        </button>
        <button type="button" aria-pressed={state.istilah === 'kesehatan'} onClick={() => dispatch({ type: 'setIstilah', istilah: 'kesehatan' })}>
          {STRINGS.istilahKesehatan}
        </button>
      </div>
      {search}
    </div>
  );
}
