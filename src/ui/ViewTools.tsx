import { useState, type Dispatch } from 'react';
import type { ViewAction, ViewState } from '../atlas/viewState';
import type { CameraPreset } from '../scene/cameraPresets';
import { STRINGS } from './strings';

const PRESETS: readonly CameraPreset[] = ['depan', 'samping', 'belakang', 'awal'];

interface Props {
  state: ViewState;
  dispatch: Dispatch<ViewAction>;
  onPreset(preset: CameraPreset): void;
}

export default function ViewTools({ state, dispatch, onPreset }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <div className={open ? 'view-tools open' : 'view-tools'}>
      <button type="button" className="tools-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        {STRINGS.camera}
      </button>
      <div className="tools-body">
        {PRESETS.map((preset) => (
          <button key={preset} type="button" onClick={() => onPreset(preset)}>
            {STRINGS[preset]}
          </button>
        ))}
        <label className="toggle">
          <input type="checkbox" checked={state.xray} onChange={(event) => dispatch({ type: 'setXray', on: event.target.checked })} />
          {STRINGS.xray}
        </label>
        <label className="slider">
          {STRINGS.explode}
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={state.explode}
            onChange={(event) => dispatch({ type: 'setExplode', amount: Number(event.target.value) })}
          />
        </label>
      </div>
    </div>
  );
}
