import type { SystemId } from '../atlas/types';
import { STRINGS } from './strings';

interface Props {
  errors: Partial<Record<SystemId, string>>;
  onRetry(system: SystemId): void;
}

export default function LayerErrorBanner({ errors, onRetry }: Props) {
  const entries = Object.entries(errors) as [SystemId, string][];
  if (!entries.length) return null;
  return (
    <div className="layer-errors" role="alert">
      {entries.map(([system, message]) => (
        <div className="layer-error" key={system}>
          <span>{message}</span>
          <button type="button" onClick={() => onRetry(system)}>
            {STRINGS.retry}
          </button>
        </div>
      ))}
    </div>
  );
}
