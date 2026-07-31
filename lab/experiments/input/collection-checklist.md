# Human Evidence Collection Checklist

Before appending any entry to `lab/experiments/input/user_responses.json`, verify all checklist items below:

- [ ] **Real Human Origin:** Response came directly from an external human user (e.g. via Reddit, Show HN, survey response).
- [ ] **Source Recorded:** Evidence source is specified (`reddit`, `hackernews`, `direct_interview`, `survey`, `landing_page`, `other`).
- [ ] **No PII:** Entry contains ZERO PII fields (`name`, `email`, `phone`, `address`, `ip`).
- [ ] **Unmodified Text:** Free text feedback is copied verbatim from user response without paraphrasing.
- [ ] **Unique Response ID:** `response_id` is unique across `user_responses.json`.
- [ ] **No Inferred Data:** Content was NOT copied or extrapolated from previous APE reports.
- [ ] **No Synthetic Payload:** `is_synthetic` is not set to `true`.
