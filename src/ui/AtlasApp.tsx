import { useMemo, useState } from 'react';
import { buildSearchIndex } from '../atlas/search';
import { systemInfo } from '../atlas/systems';
import AttributionDialog from './AttributionDialog';
import InfoPanel from './InfoPanel';
import LayerBar from './LayerBar';
import LayerErrorBanner from './LayerErrorBanner';
import SearchBox from './SearchBox';
import { fill, STRINGS } from './strings';
import TopBar from './TopBar';
import { useAtlas } from './useAtlas';
import ViewTools from './ViewTools';

export default function AtlasApp() {
  const atlas = useAtlas();
  const { state, dispatch, manifest, parts, loading } = atlas;
  const [showAttribution, setShowAttribution] = useState(false);
  const index = useMemo(() => buildSearchIndex(manifest?.parts ?? []), [manifest]);
  const selected = state.selectedId ? parts.get(state.selectedId) : undefined;
  const focusPart = (id: string) => atlas.scene.current?.focusPart(id);

  return (
    <div className="atlas">
      <div className="scene" ref={atlas.sceneRef} />
      <TopBar
        state={state}
        dispatch={dispatch}
        search={<SearchBox index={index} parts={parts} state={state} dispatch={dispatch} onFocusPart={focusPart} />}
      />
      <ViewTools state={state} dispatch={dispatch} onPreset={(preset) => atlas.scene.current?.setCameraPreset(preset)} />
      {selected && <InfoPanel part={selected} state={state} dispatch={dispatch} onFocus={focusPart} />}
      <div className="status-stack">
        {atlas.manifestError && <div className="layer-error" role="alert">{atlas.manifestError}</div>}
        <LayerErrorBanner errors={atlas.layerErrors} onRetry={atlas.retryLayer} />
        {loading && (
          <div className="loading-chip" role="status">
            {fill(STRINGS.loading, { sistem: systemInfo(loading.system).label, persen: Math.round(loading.fraction * 100) })}
          </div>
        )}
      </div>
      <LayerBar state={state} dispatch={dispatch} />
      <button type="button" className="attribution-link" onClick={() => setShowAttribution(true)}>
        {STRINGS.attribution}
      </button>
      {showAttribution && <AttributionDialog onClose={() => setShowAttribution(false)} />}
    </div>
  );
}
