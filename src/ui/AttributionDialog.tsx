import { marked } from 'marked';
import { useMemo } from 'react';
import attribution from '../../ATTRIBUTION.md?raw';
import { STRINGS } from './strings';

interface Props {
  onClose(): void;
}

export default function AttributionDialog({ onClose }: Props) {
  // ATTRIBUTION.md is part of this repository, so rendering it as HTML is safe.
  const html = useMemo(() => marked.parse(attribution, { async: false }) as string, []);
  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" role="dialog" aria-modal="true" aria-label={STRINGS.attribution} onClick={(e) => e.stopPropagation()}>
        <button type="button" className="close" aria-label={STRINGS.close} onClick={onClose}>
          ×
        </button>
        <div className="dialog-body" dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    </div>
  );
}
