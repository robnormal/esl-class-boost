// Polyfill for TextEncoder/TextDecoder which are needed by react-router-dom
// but not available in Jest's Node.js environment
import { TextEncoder, TextDecoder } from 'util';

// Add custom Jest matchers from @testing-library/jest-dom
import '@testing-library/jest-dom';

Object.assign(global, { TextDecoder, TextEncoder });
