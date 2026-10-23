import '@testing-library/jest-dom/vitest';

// jsdom has no WebGL. Report "no context" quietly instead of jsdom's "not implemented" console error.
HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;
