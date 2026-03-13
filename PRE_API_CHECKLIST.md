# YouTube Wiki Platform - Pre-API Checklist

**Status**: In Progress  
**Goal**: 100% Production Ready Before API Keys  
**Last Updated**: Feb 26, 2026

---

## How to Use This Checklist

1. Work through items in priority order (P0 = Critical, P1 = Important, P2 = Nice to have)
2. Check off items as completed: `- [x]`
3. Run verification commands after each section
4. **DO NOT proceed to API keys until all P0 items are checked**

---

## P0 - CRITICAL (Blocks API Integration)

### API Route Robustness
- [ ] Search API accepts query parameters correctly
- [ ] Search API returns consistent response format
- [ ] Search API handles empty queries gracefully
- [ ] Search API has proper error responses (400, 500)
- [ ] Chat API accepts message history correctly
- [ ] Chat API streams responses properly
- [ ] Chat API handles malformed requests
- [ ] Both APIs have CORS configured if needed
- [ ] API routes are properly typed (TypeScript)

**Verification**: 
```bash
curl -X POST http://localhost:3000/api/scotty-optimal/search \
  -H "Content-Type: application/json" \
  -d '{"query": "testosterone", "topK": 10}'

curl -X POST http://localhost:3000/api/scotty-optimal/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'
```

### Frontend API Integration
- [ ] Search component calls API on submit (not just mock)
- [ ] Search component handles loading states
- [ ] Search component displays results correctly
- [ ] Search component shows "no results" empty state
- [ ] Search component handles API errors gracefully
- [ ] Chat component calls API with streaming
- [ ] Chat component displays streaming responses
- [ ] Chat component handles API errors
- [ ] Chat component maintains message history

**Verification**: Test in browser with DevTools Network tab open

### Error Handling & Resilience
- [ ] API routes have try-catch blocks
- [ ] Frontend has error boundaries
- [ ] Network errors show user-friendly messages
- [ ] Failed requests have retry logic (at least 1 retry)
- [ ] Loading states prevent double-submission

---

## P0 - TESTING & VERIFICATION

### Build Verification
- [ ] `npm run build` completes with exit code 0
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] No ESLint warnings (`npm run lint`)
- [ ] All pages generate statically (check build output)
- [ ] No console errors in production build
- [ ] Bundle size under 500KB (check `.next/static`)

### Functional Testing
- [ ] Homepage loads correctly
- [ ] Channel page loads with correct data
- [ ] Search returns results
- [ ] Search filters work
- [ ] Chat interface opens
- [ ] Chat sends/receives messages
- [ ] Navigation between pages works
- [ ] Back button works correctly
- [ ] Refresh on any page works

### Cross-Browser Testing
- [ ] Chrome (latest) - all features work
- [ ] Firefox (latest) - all features work
- [ ] Safari (latest) - all features work
- [ ] Edge (latest) - all features work

### Mobile Responsiveness
- [ ] Homepage looks good on iPhone SE (375px)
- [ ] Homepage looks good on iPhone 14 (390px)
- [ ] Channel page works on mobile
- [ ] Search works on mobile
- [ ] Chat interface usable on mobile
- [ ] Navigation menu works on mobile
- [ ] No horizontal scrolling on mobile
- [ ] Touch targets are 44px minimum

**Verification**: Use Chrome DevTools Device Mode

---

## P1 - IMPORTANT (Production Quality)

### SEO & Meta Tags
- [ ] Homepage has proper title tag
- [ ] Homepage has meta description
- [ ] Channel pages have unique titles
- [ ] Channel pages have meta descriptions
- [ ] Open Graph tags for social sharing
- [ ] Twitter Card tags
- [ ] Favicon configured
- [ ] robots.txt created
- [ ] sitemap.xml generated

**Verification**: Use [https://metatags.io/](https://metatags.io/)

### Performance
- [ ] Lighthouse Performance score > 90
- [ ] Lighthouse Accessibility score > 90
- [ ] Lighthouse Best Practices score > 90
- [ ] Lighthouse SEO score > 90
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3.5s
- [ ] No render-blocking resources
- [ ] Images optimized (WebP format)
- [ ] Fonts preloaded

**Verification**: Run Lighthouse in Chrome DevTools

### Accessibility (a11y)
- [ ] All images have alt text
- [ ] Form inputs have associated labels
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] ARIA labels where needed
- [ ] Screen reader tested (NVDA or VoiceOver)
- [ ] No autofocus that steals focus
- [ ] Skip links for navigation

**Verification**: Use WAVE browser extension

### UX Polish
- [ ] Loading spinners on all async operations
- [ ] Empty states for no results
- [ ] Error states with helpful messages
- [ ] Success confirmations where needed
- [ ] Hover states on interactive elements
- [ ] Active states on buttons
- [ ] Smooth transitions (not jarring)
- [ ] Consistent spacing (use design system)
- [ ] Consistent colors (use CSS variables)

### State Management
- [ ] URL reflects search state (query params)
- [ ] URL reflects page state
- [ ] Browser back/forward works
- [ ] State persists on refresh where appropriate
- [ ] No prop drilling (use context if needed)

---

## P1 - DATA & CONTENT

### Mock Data Quality
- [ ] Mock episodes have realistic titles
- [ ] Mock episodes have realistic durations
- [ ] Mock topics are relevant to channel
- [ ] Mock search results make sense
- [ ] Mock chat responses are contextual
- [ ] At least 20 mock episodes per channel
- [ ] Episode IDs match real YouTube format

### Static Data Files
- [ ] `episodes.json` schema documented
- [ ] `topics.json` schema documented
- [ ] `guests.json` schema documented
- [ ] Data files validate against schema
- [ ] All channels have data files

---

## P1 - SECURITY & RELIABILITY

### Security Basics
- [ ] No secrets in client-side code
- [ ] API keys only in environment variables
- [ ] Input sanitization on API routes
- [ ] Rate limiting plan documented
- [ ] CORS policy defined

### Error Monitoring Plan
- [ ] Error tracking service chosen (Sentry?)
- [ ] Error tracking implemented
- [ ] Alert thresholds configured

### Analytics Plan
- [ ] Analytics provider chosen (Plausible? Google?)
- [ ] Privacy-compliant setup
- [ ] Key events defined (search, chat, watch)

---

## P2 - NICE TO HAVE (Can Add After API Keys)

### Additional Features
- [ ] Episode detail page
- [ ] Guest profile pages
- [ ] Topic visualization
- [ ] Search filters (date, duration, guest)
- [ ] Bookmark/save episodes
- [ ] Share functionality
- [ ] Dark mode toggle (if not default)
- [ ] Font size adjustment
- [ ] Print styles

### Developer Experience
- [ ] README.md with setup instructions
- [ ] CONTRIBUTING.md guide
- [ ] API documentation
- [ ] Component Storybook
- [ ] E2E tests (Playwright)
- [ ] Unit tests (Jest/Vitest)

### DevOps
- [ ] GitHub Actions CI/CD
- [ ] Preview deployments on PR
- [ ] Staging environment
- [ ] Production deployment checklist
- [ ] Rollback plan
- [ ] Database migration plan (for Pinecone)

---

## PRE-API VERIFICATION COMMAND

Run this before getting API keys:

```bash
#!/bin/bash
echo "=== PRE-API VERIFICATION ==="

# Build
echo "Building..."
npm run build || exit 1

# TypeScript
echo "TypeScript check..."
npx tsc --noEmit || exit 1

# Lint
echo "Linting..."
npm run lint || exit 1

# Lighthouse (manual - open in browser)
echo "Run Lighthouse in Chrome DevTools"
echo "  1. Open http://localhost:3000"
echo "  2. Open DevTools > Lighthouse"
echo "  3. Run audit"
echo "  4. Verify all scores > 90"

# Mobile testing
echo "Test on mobile:"
echo "  1. Open Chrome DevTools"
echo "  2. Toggle device toolbar"
echo "  3. Test iPhone SE, iPhone 14, iPad"

# API testing
echo "Test API routes:"
curl -s http://localhost:3000/api/scotty-optimal/search \
  -X POST -H "Content-Type: application/json" \
  -d '{"query": "test"}' | head -c 200

echo ""
echo "=== VERIFICATION COMPLETE ==="
echo "If all checks pass, you're ready for API keys!"
```

---

## CURRENT STATUS

| Category | Completed | Total | Progress |
|----------|-----------|-------|----------|
| P0 - Critical | 0 | 20 | 0% |
| P0 - Testing | 0 | 25 | 0% |
| P1 - Important | 0 | 35 | 0% |
| P2 - Nice to Have | 0 | 20 | 0% |
| **TOTAL** | **0** | **100** | **0%** |

---

## DECISION GATE

**Before getting API keys, confirm:**

- [ ] All P0 items are checked
- [ ] Build passes with zero errors
- [ ] Lighthouse scores > 90
- [ ] Mobile testing complete
- [ ] This checklist is 100% complete

**If any P0 item is unchecked = DO NOT proceed to API keys**

---

## API KEY INTEGRATION CHECKLIST (For Later)

When you're ready (after this checklist is 100%):

1. [ ] Sign up for OpenAI API
2. [ ] Sign up for Pinecone (paid tier)
3. [ ] Sign up for Gemini API
4. [ ] Add environment variables
5. [ ] Update search API to use real embeddings
6. [ ] Update chat API to use real RAG
7. [ ] Run pipeline on all channels
8. [ ] Deploy to production
9. [ ] Monitor errors
10. [ ] Celebrate! 🎉

---

**Next Action**: Start with P0 items, work top to bottom.
