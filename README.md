# Knowledge Base Inventory

| File | Type | Content Type | Approved | Poisoned | Notes |
|---|---|---|---|---|---|
| `style_guide.md` | style guide | — | ✅ | — | Brand pillars, banned words, per-content-type rules, security-handling section |
| `examples/product_launch_aurora_x3.md` | example | product_launch | ✅ | ❌ | |
| `examples/feature_announcement_night_mode.md` | example | feature_announcement | ✅ | ❌ | |
| `examples/product_campaign_trade_up.md` | example | product_campaign | ✅ | ❌ | |
| `examples/promotional_email_trade_in.md` | example | promotional_email | ✅ | ❌ | |
| `examples/software_update_os9.md` | example | software_update | ✅ | ❌ | |
| `examples/brand_campaign_designed_for_you.md` | example | brand_campaign | ✅ | ❌ | |
| `examples/social_media_launch_teaser.md` | example | social_media_post | ✅ | ❌ | |
| `examples/social_media_customer_love.md` | example | social_media_post | ✅ | ❌ | |
| `examples/poisoned_social_injection.md` | example | social_media_post | ❌ | ⚠️ **YES** | Fake `[SYSTEM: ...]` override embedded in body text; banned words; prompt-leak request |
| `briefs/brief_product_launch_aurora_x3.md` | brief | product_launch | ✅ | ❌ | |
| `briefs/brief_feature_announcement_battery.md` | brief | feature_announcement | ✅ | ❌ | |
| `briefs/brief_promotional_email_holiday.md` | brief | promotional_email | ✅ | ❌ | |
| `briefs/poisoned_brief_injection_test.md` | brief | social_media_post | ❌ | ⚠️ **YES** | Injected override + prompt-leak request inside the brief's "Constraints" field |

**Poisoned item count: 2** — one retrieved *approved example* and one submitted *brief*, covering both injection surfaces the Drafter is exposed to. This satisfies the project's 1–2 poisoned briefs/examples requirement.

All entries carry `poisoned: true/false` in their front matter so retrieval code and the KB loader can filter, tag, or exclude them programmatically rather than relying on filename alone.
