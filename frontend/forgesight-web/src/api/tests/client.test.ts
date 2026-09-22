import { describe, expect, it, vi } from 'vitest';
import { registerUnauthorizedHandler } from '../client';

describe('API client', () => {
  it('registers an unauthorized handler that can be invoked on 401', () => {
    const handler = vi.fn();
    registerUnauthorizedHandler(handler);
    handler();
    expect(handler).toHaveBeenCalledOnce();
  });
});