import { describe, it, expect } from 'vitest'
import { LLMConfig } from '../src/types'

describe('LLMConfig Type', () => {
  it('should have correct default configuration', () => {
    const config: LLMConfig = {
      provider: 'volcengine',
      model: 'doubao-pro-4k',
      endpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
      apiKey: 'test-key',
      maxTokens: 500,
      temperature: 0.7,
      topP: 0.9,
    }

    expect(config.provider).toBe('volcengine')
    expect(config.model).toBe('doubao-pro-4k')
    expect(config.maxTokens).toBe(500)
    expect(config.temperature).toBe(0.7)
  })
})
