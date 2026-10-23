import { useState } from 'react';
import { AtlasScene } from './scene/AtlasScene';
import AtlasApp from './ui/AtlasApp';
import { STRINGS } from './ui/strings';

export default function App() {
  const [supported] = useState(() => AtlasScene.isSupported());
  return (
    <div className="app">
      <header className="title-bar">
        <h1>{STRINGS.title}</h1>
      </header>
      {supported ? <AtlasApp /> : <p className="no-webgl" role="alert">{STRINGS.noWebgl}</p>}
    </div>
  );
}
