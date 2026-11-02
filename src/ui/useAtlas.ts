import { useCallback, useEffect, useMemo, useReducer, useRef, useState, type Dispatch, type RefObject } from 'react';
import { loadManifest } from '../atlas/manifest';
import { SYSTEMS, systemInfo } from '../atlas/systems';
import type { BodyManifest, PartRecord, SystemId } from '../atlas/types';
import { initialViewState, viewReducer, type ViewAction, type ViewState } from '../atlas/viewState';
import { AtlasScene } from '../scene/AtlasScene';
import { fill, STRINGS } from './strings';

const MODELS_URL = `${import.meta.env.BASE_URL}models`;

export interface AtlasHandle {
  state: ViewState;
  dispatch: Dispatch<ViewAction>;
  manifest: BodyManifest | null;
  parts: Map<string, PartRecord>;
  loading: { system: SystemId; fraction: number } | null;
  layerErrors: Partial<Record<SystemId, string>>;
  manifestError: string | null;
  retryLayer(system: SystemId): void;
  sceneRef: RefObject<HTMLDivElement | null>;
  scene: RefObject<AtlasScene | null>;
}

export function useAtlas(): AtlasHandle {
  const [state, dispatch] = useReducer(viewReducer, undefined, () => initialViewState('male'));
  const [manifest, setManifest] = useState<BodyManifest | null>(null);
  const [manifestError, setManifestError] = useState<string | null>(null);
  const [loading, setLoading] = useState<{ system: SystemId; fraction: number } | null>(null);
  const [layerErrors, setLayerErrors] = useState<Partial<Record<SystemId, string>>>({});
  const sceneRef = useRef<HTMLDivElement | null>(null);
  const scene = useRef<AtlasScene | null>(null);

  useEffect(() => {
    const container = sceneRef.current;
    if (!container) return;
    const atlas = new AtlasScene(container, {
      onPick: (id) => dispatch({ type: 'select', id }),
      onLoading: setLoading,
      onLayerError: (system) =>
        setLayerErrors((errors) => ({ ...errors, [system]: fill(STRINGS.layerError, { sistem: systemInfo(system).label }) })),
    });
    scene.current = atlas;
    return () => {
      atlas.dispose();
      scene.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setManifest(null);
    setManifestError(null);
    setLayerErrors({});
    loadManifest(state.body, MODELS_URL)
      .then((loaded) => {
        if (cancelled) return;
        scene.current?.setManifest(loaded, MODELS_URL);
        setManifest(loaded);
      })
      .catch(() => {
        if (!cancelled) setManifestError(STRINGS.manifestError);
      });
    return () => {
      cancelled = true;
    };
  }, [state.body]);

  useEffect(() => {
    if (!manifest) return;
    // Systems that failed stay unloaded until the user presses "Coba lagi" (the scene skips them too).
    const wanted = SYSTEMS.map((s) => s.id).filter((id) => state.systems[id] && !layerErrors[id]);
    void scene.current?.ensureSystems(wanted);
  }, [manifest, state.systems, layerErrors]);

  useEffect(() => {
    scene.current?.applyView(state);
  }, [state]);

  const parts = useMemo(() => new Map((manifest?.parts ?? []).map((p) => [p.id, p])), [manifest]);
  const retryLayer = useCallback((system: SystemId) => {
    scene.current?.retryLayer(system);
    setLayerErrors((errors) => {
      const next = { ...errors };
      delete next[system];
      return next;
    });
  }, []);

  return { state, dispatch, manifest, parts, loading, layerErrors, manifestError, retryLayer, sceneRef, scene };
}
