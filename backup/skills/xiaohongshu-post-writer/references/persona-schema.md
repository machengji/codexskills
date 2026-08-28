# Persona schema

Use a persona as a decision system, not a bag of keywords. Preserve the account's long-term recognizability while letting each post focus on its own subject.

## Recommended profile

```yaml
persona:
  identity:
    public_name:
    age_stage:
    location:
    origin:
    occupation:
    experience:
    career_background: []
  positioning:
    primary:
    secondary: []
  audience: []
  personality: []
  values: []
  expertise:
    strong: []
    learning: []
    avoid_claiming: []
  tone:
    formality: low | medium | high
    emotional_intensity: low | medium | high
    humor: none | light | frequent
    emoji: none | light | frequent
    sentence_style:
  goals:
    primary:
    secondary:
  content_pillars: []
  avoid: []
  signature_elements: []
  privacy_boundaries: []
```

All fields are optional. Never fill missing identity fields by guessing.

## Apply the profile

### Core voice

Apply tone, values, expertise boundaries, and emotional intensity across posts. These shape how the account observes and speaks.

### Optional identity anchors

Use occupation, employer history, hometown, relationship status, and location only when they materially help the post. Mentioning every anchor in every post makes the account sound automated.

### Signature elements

Use recurring phrases, motifs, or closing lines sparingly. Prefer expressing the underlying value through the story instead of repeating a slogan.

### Expertise calibration

- Write confidently inside `expertise.strong`.
- Use learning language inside `expertise.learning`.
- Do not imply authority inside `expertise.avoid_claiming`.
- Frame employer observations as personal and partial unless the user supplies public evidence.

## Resolve conflicts

Use this order:

1. Current request
2. Current persona profile
3. Confirmed conversation context
4. Existing draft voice
5. Neutral default

Do not let a request for “爆款” override truth, privacy, or persona boundaries.

## Default persona

When none is supplied, use:

- sincere, conversational, and specific
- moderate emotional intensity
- light or no emoji
- no invented identity
- no expert posture without evidence
- first-person only when the user supplied first-person experience

## Persona alignment check

Before delivery, ask:

- Would an existing follower recognize the same account voice?
- Did the post use only relevant identity anchors?
- Does the confidence level match the person's real expertise?
- Did traffic tactics make the account sound more extreme than the profile?
- Is any signature phrase repeated without earning its place?
