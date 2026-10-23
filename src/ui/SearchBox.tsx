import { useMemo, useState, type Dispatch } from 'react';
import { displayName } from '../atlas/names';
import { searchParts, type SearchIndex } from '../atlas/search';
import { systemInfo } from '../atlas/systems';
import type { PartRecord } from '../atlas/types';
import type { ViewAction, ViewState } from '../atlas/viewState';
import { STRINGS } from './strings';

interface Props {
  index: SearchIndex;
  parts: Map<string, PartRecord>;
  state: ViewState;
  dispatch: Dispatch<ViewAction>;
  onFocusPart?(id: string): void;
}

export default function SearchBox({ index, parts, state, dispatch, onFocusPart }: Props) {
  const [query, setQuery] = useState('');
  const results = useMemo(() => searchParts(index, query, 12), [index, query]);
  const choose = (part: PartRecord) => {
    dispatch({ type: 'revealPart', id: part.id, system: part.system });
    onFocusPart?.(part.id);
    setQuery('');
  };
  return (
    <div className="search">
      <input
        type="search"
        value={query}
        placeholder={STRINGS.searchPlaceholder}
        aria-label={STRINGS.searchPlaceholder}
        onChange={(event) => setQuery(event.target.value)}
      />
      {query.trim() !== '' &&
        (results.length ? (
          <ul role="listbox" className="search-results" aria-label={STRINGS.searchPlaceholder}>
            {results.map((id) => {
              const part = parts.get(id);
              if (!part) return null;
              return (
                <li key={id} role="option" aria-selected={false} tabIndex={0} onClick={() => choose(part)}
                  onKeyDown={(event) => event.key === 'Enter' && choose(part)}>
                  <span>{displayName(part.names, state.istilah)}</span>
                  <small>{systemInfo(part.system).label}</small>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="search-empty">{STRINGS.notFound}</p>
        ))}
    </div>
  );
}
