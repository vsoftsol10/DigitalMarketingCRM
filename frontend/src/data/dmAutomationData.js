export const MOCK_DM_AUTOMATIONS = [
  {
    id: "dma_001",
    name: "Menu Request Auto-Reply",

    organizationId: "org_001",
    organization: "Lumen Coffee Co.",

    contentId: "content_001",
    contentType: "Story",
    contentTitle: "Roastery Tour",
    contentDate: "Jul 28, 2026",

    triggerType: "Keyword",
    triggerValue: "menu",

    replyMessage:
      "Hey! Here is our full menu 📜 Tap the link in our bio to view it. Anything else I can help with?",

    status: "active",
  },
  {
    id: "dma_002",
    name: "New Follower Welcome",

    organizationId: "org_001",
    organization: "Lumen Coffee Co.",

    contentId: "content_002",
    contentType: "Reel",
    contentTitle: "New Cold Brew Drop",
    contentDate: "Aug 2, 2026",

    triggerType: "Direct Message",
    triggerValue: "",

    replyMessage:
      "Welcome to Lumen Coffee! ☕ Thanks for following. Use code WELCOME10 for 10% off your first order.",

    status: "active",
  },
  {
    id: "dma_003",
    name: "Class Information Reply",

    organizationId: "org_002",
    organization: "Atlas Fitness",

    contentId: "content_003",
    contentType: "Post",
    contentTitle: "Member Spotlight: Tara",
    contentDate: "Jul 28, 2026",

    triggerType: "Comment",
    triggerValue: "",

    replyMessage:
      "Thanks for your interest! 💪 Send us a DM and our team will help you with the class details.",

    status: "active",
  },
  {
    id: "dma_004",
    name: "Offer Request Auto-Reply",

    organizationId: "org_002",
    organization: "Atlas Fitness",

    contentId: "content_004",
    contentType: "Carousel",
    contentTitle: "Summer Membership Offer",
    contentDate: "Aug 5, 2026",

    triggerType: "Keyword",
    triggerValue: "offer",

    replyMessage:
      "Thanks for your interest! 🎉 Our summer membership offer is currently available. Send us a DM to know more.",

    status: "inactive",
  },
];

export const MOCK_INSTAGRAM_ACCOUNTS = [
  {
    id: "org_001",
    organization: "Lumen Coffee Co.",
    username: "@lumencoffee",
  },
  {
    id: "org_002",
    organization: "Atlas Fitness",
    username: "@atlasfitness",
  },
  {
    id: "org_003",
    organization: "VSoft Digital",
    username: "@vsoftdigital",
  },
];

export const MOCK_INSTAGRAM_CONTENT = [
  {
    id: "content_001",
    organizationId: "org_001",
    title: "Roastery Tour",
    type: "Reel",
    publishedAt: "Aug 2, 2026",
  },
  {
    id: "content_002",
    organizationId: "org_001",
    title: "New Cold Brew Drop",
    type: "Post",
    publishedAt: "Aug 5, 2026",
  },
  {
    id: "content_003",
    organizationId: "org_002",
    title: "Member Spotlight: Tara",
    type: "Post",
    publishedAt: "Jul 28, 2026",
  },
  {
    id: "content_004",
    organizationId: "org_002",
    title: "Summer Membership Offer",
    type: "Carousel",
    publishedAt: "Aug 5, 2026",
  },
];
