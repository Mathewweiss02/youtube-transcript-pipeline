# YouTube Wiki Platform - Pre-API Checklist (Research-Backed)

**Status**: Research Complete | Implementation In Progress  
**Goal**: 100% Production Ready Before API Keys  
**Last Updated**: Feb 26, 2026
**Sources**: Context7 (Next.js, React, Playwright, Lighthouse), DeepWiki (vercel/next.js)

---

## Research Summary

This checklist incorporates best practices from:
- **Next.js Official Docs** (Route Handlers, App Router, Streaming)
- **React 18+ Best Practices** (Error Boundaries, Streaming)
- **Playwright Testing** (E2E, Cross-browser, Mobile)
- **Lighthouse CI** (Performance Budgets, Accessibility)
- **Vercel AI SDK** (Streaming patterns)

---

## P0 - CRITICAL (Blocks API Integration)

### 1. API Route Robustness

#### 1.1 Search API - Proper Implementation
**Research Source**: Context7 Next.js Route Handlers + DeepWiki best practices

**Requirements**:
- [ ] Accept query parameters via `request.json()`
- [ ] Validate input (zod recommended)
- [ ] Return consistent response format
- [ ] Handle empty queries (400 error)
- [ ] Proper error responses (500 for server errors)
- [ ] TypeScript types for request/response

**Verified Code Pattern**:
```typescript
// app/api/[channel]/search/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const searchSchema = z.object({
  query: z.string().min(1).max(200),
  topK: z.number().min(1).max(50).default(10),
});

type SearchRequest = z.infer<typeof searchSchema>;

interface SearchResult {
  id: string;
  title: string;
  url: string;
  topics: string[];
  score: number;
  snippet?: string;
  timestamp: number;
}

interface SearchResponse {
  results: SearchResult[];
  query: string;
  total: number;
  metadata: {
    processingTime: number;
    source: string;
  };
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ channel: string }> }
): Promise<NextResponse<SearchResponse | { error: string }>> {
  const startTime = Date.now();
  
  try {
    const { channel } = await params;
    const body = await request.json();
    
    // Validate input
    const validation = searchSchema.safeParse(body);
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid request: ' + validation.error.message },
        { status: 400 }
      );
    }
    
    const { query, topK } = validation.data;
    
    // TODO: Replace with actual Pinecone search
    // const embedding = await generateEmbedding(query);
    // const results = await pinecone.query(channel, embedding, topK);
    
    const mockResults: SearchResult[] = []; // Your mock data
    
    return NextResponse.json({
      results: mockResults,
      query,
      total: mockResults.length,
      metadata: {
        processingTime: Date.now() - startTime,
        source: 'mock'
      }
    }, { status: 200 });
    
  } catch (error) {
    console.error('Search error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**Verification Command**:
```bash
curl -X POST http://localhost:3000/api/scotty-optimal/search \
  -H "Content-Type: application/json" \
  -d '{"query": "testosterone", "topK": 10}' \
  -v
```

**Expected**: HTTP 200 with JSON results

---

#### 1.2 Chat API - Streaming Implementation
**Research Source**: Context7 Next.js Streaming + Vercel AI SDK patterns

**Requirements**:
- [ ] Accept message history
- [ ] Stream responses using ReadableStream
- [ ] Handle malformed requests
- [ ] Proper error handling
- [ ] Connection cleanup on error

**Verified Code Pattern**:
```typescript
// app/api/[channel]/chat/route.ts
import { NextRequest } from 'next/server';
import { z } from 'zod';

const chatSchema = z.object({
  messages: z.array(z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string().min(1).max(4000)
  })).min(1)
});

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ channel: string }> }
): Promise<Response> {
  try {
    const { channel } = await params;
    const body = await request.json();
    
    const validation = chatSchema.safeParse(body);
    if (!validation.success) {
      return new Response(
        JSON.stringify({ error: 'Invalid request: ' + validation.error.message }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }
    
    const { messages } = validation.data;
    const userMessage = messages[messages.length - 1];
    
    // TODO: Replace with actual RAG + Gemini
    // const context = await retrieveContext(channel, userMessage.content);
    // const stream = await gemini.stream({ messages, context });
    
    // Mock streaming for now
    const encoder = new TextEncoder();
    const mockResponse = `Based on ${channel} content: ${userMessage.content}`;
    
    const stream = new ReadableStream({
      async start(controller) {
        const words = mockResponse.split(' ');
        for (const word of words) {
          controller.enqueue(encoder.encode(word + ' '));
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        controller.close();
      }
    });
    
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
        'X-Channel': channel
      }
    });
    
  } catch (error) {
    console.error('Chat error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
```

**Verification Command**:
```bash
curl -X POST http://localhost:3000/api/scotty-optimal/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}' \
  -v --no-buffer
```

**Expected**: Streaming text response

---

### 2. Frontend API Integration

#### 2.1 Search Component with Full State Management
**Research Source**: React useState patterns + error handling

**Requirements**:
- [ ] Controlled input with state
- [ ] Loading state during API call
- [ ] Error state display
- [ ] Empty state handling
- [ ] Results display
- [ ] URL query synchronization (optional)

**Verified Code Pattern**:
```typescript
'use client';

import { useState, useCallback } from 'react';
import { Search, Loader2, AlertCircle } from 'lucide-react';

interface SearchResult {
  id: string;
  title: string;
  url: string;
  topics: string[];
  score: number;
  snippet?: string;
}

interface UseSearchOptions {
  channel: string;
  onError?: (error: string) => void;
}

function useSearch({ channel, onError }: UseSearchOptions) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      setHasSearched(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await fetch(`/api/${channel}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, topK: 10 })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Search failed: ${response.status}`);
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setError(message);
      onError?.(message);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [channel, onError]);

  return { results, isLoading, error, hasSearched, search };
}

// Component usage
export function SearchComponent({ channel }: { channel: string }) {
  const [query, setQuery] = useState('');
  const { results, isLoading, error, hasSearched, search } = useSearch({ channel });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    search(query);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search episodes, topics..."
          className="w-full pl-10 pr-12 py-3 rounded-lg border border-slate-200"
          disabled={isLoading}
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin" />
        )}
      </form>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {hasSearched && results.length === 0 && !error && (
        <div className="text-center py-8 text-slate-500">
          <p>No results found for &quot;{query}&quot;</p>
          <p className="text-sm mt-1">Try different keywords or check spelling</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-slate-500">
            Found {results.length} result{results.length !== 1 ? 's' : ''}
          </p>
          {/* Results display */}
        </div>
      )}
    </div>
  );
}
```

---

#### 2.2 Chat Component with Streaming Support
**Research Source**: React streaming patterns, use hook

**Requirements**:
- [ ] Streaming message display
- [ ] Error handling with retry
- [ ] Message history maintenance
- [ ] Loading states
- [ ] Abort controller for cleanup

**Verified Code Pattern**:
```typescript
'use client';

import { useState, useRef, useCallback } from 'react';
import { Send, Bot, User, AlertCircle } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
}

function useChat(channel: string) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I can answer questions about this channel\'s content.'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Cancel previous request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setStreamingContent('');

    try {
      const response = await fetch(`/api/${channel}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          }))
        }),
        signal: abortRef.current.signal
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed: ${response.status}`);
      }

      // Handle streaming
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      let fullContent = '';
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullContent += chunk;
        setStreamingContent(fullContent);
      }

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: fullContent
      }]);
      setStreamingContent('');

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      
      const message = err instanceof Error ? err.message : 'Failed to get response';
      setError(message);
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [channel, messages]);

  return {
    messages,
    isLoading,
    error,
    streamingContent,
    sendMessage
  };
}
```

---

### 3. Error Boundaries

**Research Source**: React Error Boundaries documentation

**Requirements**:
- [ ] Class component error boundary
- [ ] Fallback UI component
- [ ] Error logging
- [ ] Reset capability

**Verified Code Pattern**:
```typescript
// components/error-boundary.tsx
'use client';

import { Component, type ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to error tracking service
    console.error('ErrorBoundary caught error:', error, errorInfo);
    // TODO: Send to Sentry/DataDog/etc
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h2 className="text-lg font-semibold text-red-900">
              Something went wrong
            </h2>
          </div>
          <p className="text-red-700 mb-4">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <RefreshCw className="w-4 h-4" />
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## P0 - TESTING & VERIFICATION

### 4. Build Verification

**Research Source**: Next.js build process, TypeScript, ESLint

**Automated Verification Script**:
```bash
#!/bin/bash
set -e

echo "🔍 Pre-API Build Verification"
echo "=============================="

# 1. TypeScript
echo "📘 TypeScript check..."
npx tsc --noEmit
echo "✅ TypeScript passed"

# 2. ESLint
echo "🔧 ESLint check..."
npm run lint
echo "✅ ESLint passed"

# 3. Build
echo "🏗️  Building..."
npm run build
echo "✅ Build successful"

# 4. Check bundle size
echo "📦 Bundle size check..."
BUNDLE_SIZE=$(du -sh .next/static | cut -f1)
echo "Bundle size: $BUNDLE_SIZE"

# 5. Verify static generation
echo "📄 Checking static pages..."
if [ -d ".next/server/app/channel" ]; then
  echo "✅ Static pages generated"
else
  echo "❌ Static pages missing"
  exit 1
fi

echo ""
echo "🎉 All verification checks passed!"
echo "Ready for API key integration."
```

---

### 5. E2E Testing with Playwright

**Research Source**: Playwright best practices, cross-browser testing

**Playwright Configuration**:
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

**Test Examples**:
```typescript
// e2e/search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Search', () => {
  test('should return results for valid query', async ({ page }) => {
    await page.goto('/channel/scotty-optimal');
    await page.fill('[type="search"]', 'testosterone');
    await page.press('[type="search"]', 'Enter');
    
    await expect(page.locator('text=Search Results')).toBeVisible();
    await expect(page.locator('[role="listitem"]')).toHaveCount.greaterThan(0);
  });

  test('should show empty state for no results', async ({ page }) => {
    await page.goto('/channel/scotty-optimal');
    await page.fill('[type="search"]', 'xyznonexistent');
    await page.press('[type="search"]', 'Enter');
    
    await expect(page.locator('text=No results found')).toBeVisible();
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Simulate API error
    await page.route('**/api/*/search', route => route.abort('failed'));
    
    await page.goto('/channel/scotty-optimal');
    await page.fill('[type="search"]', 'test');
    await page.press('[type="search"]', 'Enter');
    
    await expect(page.locator('text=Search failed')).toBeVisible();
  });
});

// e2e/chat.spec.ts
test.describe('Chat', () => {
  test('should send and receive messages', async ({ page }) => {
    await page.goto('/channel/scotty-optimal/chat');
    
    await page.fill('[placeholder*="Ask"]', 'What is testosterone?');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=What is testosterone?')).toBeVisible();
    await expect(page.locator('.streaming-message')).toBeVisible();
  });
});
```

---

## P1 - IMPORTANT (Production Quality)

### 6. Performance & Lighthouse

**Research Source**: Lighthouse CI, Performance Budgets

**Lighthouse CI Configuration**:
```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      startServerCommand: 'npm run start',
      url: ['http://localhost:3000/', 'http://localhost:3000/channel/scotty-optimal'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'first-contentful-paint': ['error', { maxNumericValue: 1500 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

**GitHub Actions Workflow**:
```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI

on: [push]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run build
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
```

---

### 7. SEO & Meta Tags

**Research Source**: Next.js metadata API

**Dynamic Metadata**:
```typescript
// app/channel/[channel]/page.tsx
import { Metadata } from 'next';

export async function generateMetadata({ params }: { params: { channel: string } }): Promise<Metadata> {
  const channel = await getChannel(params.channel);
  
  return {
    title: `${channel.name} Wiki | YouTube Knowledge Base`,
    description: channel.description,
    openGraph: {
      title: `${channel.name} Wiki`,
      description: channel.description,
      type: 'website',
      images: [`/api/og?channel=${channel.slug}`], // Dynamic OG image
    },
    twitter: {
      card: 'summary_large_image',
      title: `${channel.name} Wiki`,
      description: channel.description,
    },
    alternates: {
      canonical: `/channel/${channel.slug}`,
    },
  };
}
```

**Sitemap Generation**:
```typescript
// app/sitemap.ts
import { MetadataRoute } from 'next';
import { getAllChannels } from '@/lib/channels';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const channels = await getAllChannels();
  
  return [
    {
      url: 'https://youtubewiki.com',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    ...channels.map(channel => ({
      url: `https://youtubewiki.com/channel/${channel.slug}`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.8,
    })),
  ];
}
```

---

## VERIFICATION CHECKLIST

### Pre-API Readiness Gate

**Must Pass All Before API Keys**:

| # | Check | Command | Pass Criteria |
|---|-------|---------|---------------|
| 1 | TypeScript | `npx tsc --noEmit` | 0 errors |
| 2 | ESLint | `npm run lint` | 0 errors, 0 warnings |
| 3 | Build | `npm run build` | Exit 0, no errors |
| 4 | Unit Tests | `npm test` | 100% pass |
| 5 | E2E Tests | `npx playwright test` | 100% pass |
| 6 | Lighthouse | `lhci autorun` | All scores >90 |
| 7 | API Test - Search | `curl -X POST /api/*/search` | HTTP 200, JSON response |
| 8 | API Test - Chat | `curl -X POST /api/*/chat` | Streaming response |
| 9 | Mobile Test | Chrome DevTools | No layout issues |
| 10 | Accessibility | axe-core / WAVE | 0 violations |

**Decision Gate**:
- ✅ All 10 checks pass = Ready for API keys
- ❌ Any check fails = Fix before proceeding

---

## CURRENT STATUS

| Category | Items | Completed | Progress |
|----------|-------|-----------|----------|
| P0 - API Routes | 2 | 0 | 0% |
| P0 - Frontend | 2 | 0 | 0% |
| P0 - Testing | 10 | 0 | 0% |
| P1 - Performance | 4 | 0 | 0% |
| P1 - SEO | 3 | 0 | 0% |
| **TOTAL** | **21** | **0** | **0%** |

**Next Action**: Implement API routes with proper error handling (Section 1.1 & 1.2)
